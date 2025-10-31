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

# API endpoint (default to 0.0.0.0:8001, can be overridden by environment variable)
API_URL = os.getenv("API_URL", "http://localhost:8080")


def format_sources(sources: List[dict]) -> str:
    """Format source documents for display"""
    if not sources:
        return "\n\n**No sources available**"
    
    formatted = "\n\n### 📚 Sources:\n\n"
    for i, source in enumerate(sources, 1):
        title = source.get("title", "Unknown")
        distance = source.get("distance", 0)
        similarity = (1 - distance) * 100  # Convert distance to similarity percentage
        text_preview = source.get("text", "")[:200] + "..." if len(source.get("text", "")) > 200 else source.get("text", "")
        
        formatted += f"**{i}. {title}** (Relevance: {similarity:.1f}%)\n"
        formatted += f"> {text_preview}\n\n"
    
    return formatted


def query_api(question: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Query the FastAPI backend and return the answer with sources.
    """
    if not question.strip():
        return "", history
    
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
            
            # Format response with sources
            full_response = answer + format_sources(sources)
            
            # Update history
            history.append((question, full_response))
            
            return "", history
        else:
            error_msg = f"❌ Error: {response.status_code} - {response.text}"
            history.append((question, error_msg))
            return "", history
            
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out. The query is taking too long. Please try again."
        history.append((question, error_msg))
        return "", history
        
    except requests.exceptions.ConnectionError:
        error_msg = f"🔌 Cannot connect to API at {API_URL}. Make sure the backend is running."
        history.append((question, error_msg))
        return "", history
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append((question, error_msg))
        return "", history


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
            
            if status == "healthy":
                return "✅ API is running and healthy"
            else:
                return f"⚠️ API Status: {status}\n- Weaviate: {'✓' if weaviate_ready else '✗'}\n- Collection: {'✓' if collection_available else '✗'}"
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
        .chatbot {height: 500px !important;}
    """
) as demo:
    
    gr.Markdown(
        """
        # 🏥 ISO Medical Device Documents Assistant
        
        Ask questions about ISO standards and medical device regulations. 
        The assistant uses RAG (Retrieval Augmented Generation) to provide accurate answers based on:
        
        - ISO 13485 (Quality Management)
        - ISO 14971 (Risk Management)
        - ISO 14155 (Clinical Investigation)
        - ISO 62304 (Medical Device Software)
        - ISO 15223-1 (Symbols)
        - EU MDR 2017/745
        - MDCG Guidance Documents
        """
    )
    
    # Status indicator
    with gr.Row():
        status_box = gr.Textbox(
            label="API Status",
            value=check_api_status(),
            interactive=False,
            lines=2
        )
        refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    refresh_btn.click(fn=check_api_status, outputs=status_box)
    
    # Main chat interface
    with gr.Tab("💬 Chat Assistant"):
        chatbot = gr.Chatbot(
            label="ISO Documents Assistant",
            height=500,
            bubble_full_width=False,
            avatar_images=(None, "🤖")
        )
        
        with gr.Row():
            question_input = gr.Textbox(
                label="Ask a question",
                placeholder="e.g., What are the requirements for risk management in medical devices?",
                lines=2,
                scale=4
            )
            submit_btn = gr.Button("Send", variant="primary", scale=1)
        
        gr.Examples(
            examples=[
                "What are the key requirements for medical device software according to ISO 62304?",
                "What is the difference between Class I and Class III medical devices?",
                "What are the clinical investigation requirements for medical devices?",
                "Explain the risk management process according to ISO 14971",
                "What documentation is required for CE marking under EU MDR?"
            ],
            inputs=question_input,
            label="Example Questions"
        )
        
        clear_btn = gr.Button("🗑️ Clear Chat")
        
        # Set up event handlers
        submit_btn.click(
            fn=query_api,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot]
        )
        
        question_input.submit(
            fn=query_api,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot]
        )
        
        clear_btn.click(fn=lambda: [], outputs=chatbot)
    
    # Search interface
    with gr.Tab("🔍 Search Documents"):
        gr.Markdown("Search for specific topics in the ISO documents using semantic search.")
        
        with gr.Row():
            search_input = gr.Textbox(
                label="Search Query",
                placeholder="e.g., software validation",
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
    
    # Info tab
    with gr.Tab("ℹ️ About"):
        gr.Markdown(
            """
            ## About This Application
            
            This chatbot provides intelligent access to ISO medical device standards and regulations.
            
            ### Features:
            - **RAG-Powered Answers**: Uses Retrieval Augmented Generation for accurate responses
            - **Source Citations**: Every answer includes references to source documents
            - **Semantic Search**: Find relevant information across all documents
            - **GPT-4o Integration**: Powered by OpenAI's latest model
            
            ### Technology Stack:
            - **Backend**: FastAPI with Weaviate vector database
            - **Embeddings**: OpenAI text-embedding-3-large
            - **LLM**: GPT-4o
            - **Frontend**: Gradio
            
            ### Available Documents:
            - ISO 13485:2016 - Quality Management Systems
            - ISO 14971:2019 - Risk Management
            - ISO 14155:2020 - Clinical Investigation
            - ISO 62304:2006 - Medical Device Software
            - ISO 15223-1:2021 - Symbols for Medical Devices
            - EU MDR 2017/745 - Medical Device Regulation
            - MDCG 2020-3 - Clinical Evaluation Guidelines
            
            ### Notes:
            - Responses are based on the content of indexed documents
            - Always verify critical compliance information with official standards
            - The system processes ~4,000 document chunks for comprehensive coverage
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
