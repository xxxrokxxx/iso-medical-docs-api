"""
Gradio chatbot frontend for ISO Medical Device Documents Query System.
Connects to FastAPI backend for RAG-based question answering.
"""

import os
import gradio as gr
import requests
from typing import List, Tuple
from dotenv import load_dotenv

load_dotenv()

# API endpoint (default to localhost:8080, can be overridden by environment variable)
API_URL = os.getenv("API_URL", "http://localhost:8080")


def format_sources(sources: List[dict]) -> str:
    """Format source documents for display"""
    if not sources:
        return "No sources available"
    
    formatted = ""
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Unknown")
        distance = source.get("distance", 0)
        similarity = (1 - distance) * 100  # Convert distance to similarity percentage
        text_preview = source.get("text", "")[:300] + "..." if len(source.get("text", "")) > 300 else source.get("text", "")
        source_file = source.get("source", "Unknown source")
        
        formatted += f"### Source {i}: {title}\n"
        formatted += f"**Relevance:** {similarity:.1f}%\n\n"
        formatted += f"{text_preview}\n\n"
        formatted += f"*File: {source_file}*\n\n"
        formatted += "---\n\n"
    
    return formatted


def query_api(question: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]], str]:
    """
    Query the FastAPI backend and return the answer with sources separately.
    """
    if not question.strip():
        return "", history, ""
    
    try:
        # Make request to FastAPI backend
        response = requests.post(
            f"{API_URL}/ask",
            json={"question": question, "limit": 3},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No answer generated")
            sources = data.get("sources", [])
            
            # Format sources separately
            sources_text = format_sources(sources)
            
            # Update chat history with just the answer
            history.append((question, answer))
            
            return "", history, sources_text
        else:
            error_msg = f"❌ Error: {response.status_code} - {response.text}"
            history.append((question, error_msg))
            return "", history, ""
            
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out. The query is taking too long. Please try again."
        history.append((question, error_msg))
        return "", history, ""
        
    except requests.exceptions.ConnectionError:
        error_msg = f"🔌 Cannot connect to API at {API_URL}. Make sure the backend is running."
        history.append((question, error_msg))
        return "", history, ""
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append((question, error_msg))
        return "", history, ""


def search_documents(query: str, limit: int = 5) -> str:
    """
    Search documents using semantic search.
    """
    if not query.strip():
        return "Please enter a search query."
    
    try:
        response = requests.post(
            f"{API_URL}/search",
            json={"query": query, "limit": limit},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            
            if not results:
                return "No results found."
            
            formatted = f"### 🔍 Search Results for: '{query}'\n\n"
            formatted += f"Found {len(results)} relevant documents:\n\n"
            
            for i, result in enumerate(results, 1):
                title = result.get("title", "Unknown")
                distance = result.get("distance", 0)
                similarity = (1 - distance) * 100
                text = result.get("text", "")[:300] + "..." if len(result.get("text", "")) > 300 else result.get("text", "")
                
                formatted += f"**{i}. {title}** (Relevance: {similarity:.1f}%)\n\n"
                formatted += f"{text}\n\n"
                formatted += "---\n\n"
            
            return formatted
        else:
            return f"❌ Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


def check_api_status() -> str:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            weaviate_ready = data.get("weaviate_ready", False)
            collection_available = data.get("collection_available", False)
            
            status_text = f"""### API Status: {'✅ Healthy' if status == 'healthy' else '⚠️ ' + status}

**Backend:** {API_URL}
**Weaviate:** {'✅ Connected' if weaviate_ready else '❌ Not connected'}
**Collection:** {'✅ Available' if collection_available else '❌ Not available'}
**Documents:** ~4,000 indexed chunks
"""
            return status_text
        else:
            return f"❌ API returned status code: {response.status_code}"
    except Exception as e:
        return f"❌ Cannot connect to API: {str(e)}"


# Create Gradio interface
with gr.Blocks(
    title="ISO Medical Device Documents Assistant",
    theme=gr.themes.Soft(),
    css="""
        .gradio-container {font-family: 'Arial', sans-serif;}
        .info-box {background-color: #f0f7ff; padding: 15px; border-radius: 8px; margin-bottom: 20px;}
    """
) as demo:
    
    gr.Markdown(
        """
        # 🏥 ISO Medical Device Documents Assistant
        
        Ask questions about ISO standards and medical device regulations using AI-powered search.
        
        **💡 Tip:** Ask specific questions for better results. Every answer includes source references.
        """,
        elem_classes="info-box"
    )
    
    # Main tabs
    with gr.Tab("💬 Chat Assistant"):
        with gr.Row():
            # Left column - Chat
            with gr.Column(scale=2):
                gr.Markdown("### Ask Your Question")
                
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=400,
                    show_copy_button=True
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., What are the key requirements for risk management in medical devices?",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                
                clear_btn = gr.Button("🗑️ Clear Chat", size="sm")
                
                gr.Markdown("### Example Questions")
                gr.Examples(
                    examples=[
                        "What are the key requirements for medical device software according to ISO 62304?",
                        "What is the difference between Class I and Class III medical devices?",
                        "What are the clinical investigation requirements for medical devices?",
                        "Explain the risk management process according to ISO 14971",
                        "What documentation is required for CE marking under EU MDR?"
                    ],
                    inputs=question_input,
                )
            
            # Right column - References
            with gr.Column(scale=1):
                gr.Markdown("### 📖 Source References")
                sources_output = gr.Markdown(
                    value="*Sources will appear here after you ask a question*",
                    label="References"
                )
        
        # Set up event handlers
        submit_btn.click(
            fn=query_api,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sources_output]
        )
        
        question_input.submit(
            fn=query_api,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sources_output]
        )
        
        clear_btn.click(
            fn=lambda: ([], "*Sources will appear here after you ask a question*"),
            outputs=[chatbot, sources_output]
        )
    
    # Search interface
    with gr.Tab("🔍 Search Documents"):
        gr.Markdown("### Semantic Search")
        gr.Markdown("Search for specific topics across all ISO documents using semantic similarity.")
        
        with gr.Row():
            search_input = gr.Textbox(
                label="Search Query",
                placeholder="e.g., software validation, risk assessment, clinical trials",
                lines=1,
                scale=3
            )
            search_limit = gr.Slider(
                minimum=1,
                maximum=10,
                value=5,
                step=1,
                label="Number of Results",
                scale=1
            )
            search_btn = gr.Button("Search", variant="primary", scale=1)
        
        search_output = gr.Markdown(label="Search Results")
        
        search_btn.click(
            fn=search_documents,
            inputs=[search_input, search_limit],
            outputs=search_output
        )
        
        search_input.submit(
            fn=search_documents,
            inputs=[search_input, search_limit],
            outputs=search_output
        )
    
    # About tab
    with gr.Tab("ℹ️ About"):
        with gr.Row():
            with gr.Column():
                gr.Markdown(
                    """
                    ## About This Application
                    
                    This intelligent chatbot provides access to ISO medical device standards and regulations 
                    using advanced AI technology.
                    
                    ### 📚 Available Standards
                    
                    This assistant provides answers based on the following ISO standards and regulations:
                    
                    - **ISO 13485** - Quality Management Systems
                    - **ISO 14971** - Risk Management for Medical Devices
                    - **ISO 14155** - Clinical Investigation of Medical Devices
                    - **ISO 62304** - Medical Device Software Life Cycle Processes
                    - **ISO 15223-1** - Symbols to be Used with Information
                    - **EU MDR 2017/745** - Medical Device Regulation
                    - **MDCG 2020-3** - Clinical Evaluation Guidelines
                    
                    ### 🎯 Features
                    
                    - **RAG-Powered Answers**: Retrieval Augmented Generation ensures accuracy
                    - **Source Citations**: Every answer includes document references
                    - **Semantic Search**: Find information using natural language
                    - **4,000+ Document Chunks**: Comprehensive coverage of standards
                    - **Real-time Responses**: Powered by GPT-4o
                    
                    ### 🛠️ Technology Stack
                    
                    - **Backend**: FastAPI + Weaviate Vector Database
                    - **Embeddings**: OpenAI text-embedding-3-large
                    - **LLM**: GPT-4o (OpenAI)
                    - **Frontend**: Gradio
                    - **Deployment**: Google Cloud Run
                    
                    ### ⚠️ Important Notes
                    
                    - Responses are based on indexed document content
                    - Always verify critical compliance information with official standards
                    - This tool is for informational purposes
                    - Last updated: October 2025
                    
                    ### 📊 API Status
                    """
                )
                
                status_output = gr.Markdown(value=check_api_status())
                refresh_status_btn = gr.Button("🔄 Refresh API Status")
                
                refresh_status_btn.click(fn=check_api_status, outputs=status_output)
                
                gr.Markdown(
                    """
                    ---
                    
                    ### 🔗 Resources
                    
                    - [ISO Official Website](https://www.iso.org)
                    - [EU MDR Portal](https://ec.europa.eu/health/md_sector/overview_en)
                    - [GitHub Repository](https://github.com/xxxrokxxx/iso-medical-docs-api)
                    """
                )


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("GRADIO_PORT", 7860))
    
    # Launch the app
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
