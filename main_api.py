"""
FastAPI backend for querying ISO medical device documents in Weaviate.
Provides endpoints for semantic search and RAG-based question answering.
"""

import os
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Weaviate imports
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose logs
logging.getLogger("weaviate").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="ISO Medical Device Documents API",
    description="Query ISO standards and medical device regulations using RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Weaviate client
client = None
collection = None


class SearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Search query text", min_length=1)
    limit: int = Field(5, description="Number of results to return", ge=1, le=20)


class RAGRequest(BaseModel):
    """Request model for RAG question answering"""
    question: str = Field(..., description="Question to answer", min_length=1)
    limit: int = Field(3, description="Number of context chunks to use", ge=1, le=10)


class SearchResult(BaseModel):
    """Response model for search results"""
    text: str
    title: str
    source: str
    distance: float


class RAGResponse(BaseModel):
    """Response model for RAG answers"""
    answer: str
    sources: List[SearchResult]
    question: str


def init_weaviate():
    """Initialize and return a Weaviate client connected to Weaviate Cloud."""
    try:
        # Get environment variables
        voyageai_key = os.getenv("VOYAGEAI_APIKEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        wcd_url = os.getenv("WEAVIATE_URL")
        wcd_api_key = os.getenv("WEAVIATE_API_KEY")

        if not all([openai_api_key, wcd_url, wcd_api_key]):
            missing_vars = []
            if not openai_api_key:
                missing_vars.append("OPENAI_API_KEY")
            if not wcd_url:
                missing_vars.append("WEAVIATE_URL")
            if not wcd_api_key:
                missing_vars.append("WEAVIATE_API_KEY")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        headers = {
            "X-Openai-Api-Key": openai_api_key,
        }
        
        # Add VoyageAI key if available
        if voyageai_key:
            headers["X-VoyageAI-Api-Key"] = voyageai_key

        logger.info(f"Connecting to Weaviate Cloud at: {wcd_url}")

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=wcd_url,
            auth_credentials=Auth.api_key(wcd_api_key),
            headers=headers
        )

        if client.is_ready():
            logger.info("✓ Weaviate connection successful!")
        else:
            logger.warning("WARNING: Weaviate client connected but reports not ready.")

        return client

    except Exception as e:
        logger.error(f"Error initializing Weaviate: {str(e)}")
        raise


@app.on_event("startup")
async def startup_event():
    """Initialize Weaviate client on startup"""
    global client, collection
    
    try:
        logger.info("Starting up ISO Documents API...")
        client = init_weaviate()
        
        # Get the collection
        collection = client.collections.get("ISODocuments")
        logger.info("✓ Connected to ISODocuments collection")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close Weaviate client on shutdown"""
    global client
    
    if client:
        logger.info("Shutting down and closing Weaviate client...")
        client.close()
        logger.info("✓ Client closed")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ISO Medical Device Documents API",
        "version": "1.0.0",
        "status": "running",
        "collection": "ISODocuments",
        "endpoints": {
            "/search": "Semantic search in ISO documents",
            "/ask": "RAG-based question answering",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global client, collection
    
    try:
        is_ready = client.is_ready() if client else False
        has_collection = collection is not None
        
        return {
            "status": "healthy" if (is_ready and has_collection) else "degraded",
            "weaviate_ready": is_ready,
            "collection_available": has_collection
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchRequest):
    """
    Perform semantic search in ISO documents.
    
    Returns relevant document chunks based on semantic similarity.
    """
    global collection
    
    if not collection:
        raise HTTPException(status_code=503, detail="Collection not available")
    
    try:
        logger.info(f"Searching for: {request.query}")
        
        # Perform semantic search
        response = collection.query.near_text(
            query=request.query,
            limit=request.limit,
            return_metadata=MetadataQuery(distance=True),
            return_properties=["text", "title", "source"]
        )
        
        # Format results
        results = []
        for obj in response.objects:
            results.append(SearchResult(
                text=obj.properties.get("text", ""),
                title=obj.properties.get("title", ""),
                source=obj.properties.get("source", ""),
                distance=obj.metadata.distance if obj.metadata.distance else 1.0
            ))
        
        logger.info(f"Found {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/ask", response_model=RAGResponse)
async def ask_question(request: RAGRequest):
    """
    Answer questions using RAG over ISO documents.
    
    Uses GPT-4o to generate answers based on retrieved document chunks.
    """
    global collection
    
    if not collection:
        raise HTTPException(status_code=503, detail="Collection not available")
    
    try:
        logger.info(f"Question: {request.question}")
        
        # Create prompt for RAG
        prompt = """Based on the retrieved context from ISO medical device standards and regulations, 
answer the following question accurately and concisely. If the context doesn't contain enough 
information to answer the question, say so.

Question: {question}

Context: {text}

Answer:"""
        
        # Perform RAG query
        response = collection.generate.near_text(
            query=request.question,
            limit=request.limit,
            grouped_task=prompt.replace("{question}", request.question),
            return_metadata=MetadataQuery(distance=True),
            return_properties=["text", "title", "source"]
        )
        
        # Get the generated answer
        answer = response.generated if response.generated else "No answer could be generated."
        
        # Format source documents
        sources = []
        for obj in response.objects:
            sources.append(SearchResult(
                text=obj.properties.get("text", ""),
                title=obj.properties.get("title", ""),
                source=obj.properties.get("source", ""),
                distance=obj.metadata.distance if obj.metadata.distance else 1.0
            ))
        
        logger.info(f"Generated answer with {len(sources)} sources")
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            question=request.question
        )
        
    except Exception as e:
        logger.error(f"RAG error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
