"""
Create a Weaviate collection with ISO medical device documents using Docling for PDF parsing.
Combines Weaviate client initialization, Docling PDF conversion, and collection creation.
"""

import os
import json
from pathlib import Path
import logging
from dotenv import load_dotenv

# Weaviate imports
import weaviate
from weaviate.classes.init import Auth
import weaviate.classes.config as wc

# Docling imports
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker import HierarchicalChunker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress Weaviate client debug logs
logging.getLogger("weaviate").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()


def init_weaviate():
    """
    Initialize and return a Weaviate client connected to Weaviate Cloud.
    """
    try:
        # Get environment variables
        voyageai_key = os.getenv("VOYAGEAI_APIKEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        wcd_url = os.getenv("WEAVIATE_URL")
        wcd_api_key = os.getenv("WEAVIATE_API_KEY")

        if not all([voyageai_key, openai_api_key, wcd_url, wcd_api_key]):
            missing_vars = []
            if not voyageai_key:
                missing_vars.append("VOYAGEAI_APIKEY")
            if not openai_api_key:
                missing_vars.append("OPENAI_API_KEY")
            if not wcd_url:
                missing_vars.append("WEAVIATE_URL")
            if not wcd_api_key:
                missing_vars.append("WEAVIATE_API_KEY")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        headers = {
            "X-VoyageAI-Api-Key": voyageai_key,
            "X-Openai-Api-Key": openai_api_key,
        }

        logger.info(f"Connecting to Weaviate Cloud at: {wcd_url}")

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=wcd_url,
            auth_credentials=Auth.api_key(wcd_api_key),
            headers=headers
        )

        # Check if the client is ready
        if client.is_ready():
            logger.info("✓ Weaviate connection successful! Client is ready.")
        else:
            logger.warning("WARNING: Weaviate client connected but reports not ready.")

        return client

    except Exception as e:
        logger.error(f"Error initializing Weaviate: {str(e)}")
        raise


def get_pdf_documents():
    """
    Get list of PDF documents from the docs directory.
    """
    docs_dir = Path(__file__).parent / "docs"
    
    # Create a list of source documents from the docs directory
    source_docs = [
        str(docs_dir / filename) 
        for filename in os.listdir(docs_dir) 
        if filename.endswith('.pdf')
    ]
    
    logger.info(f"Found {len(source_docs)} PDF documents:")
    for doc in source_docs:
        logger.info(f"  - {Path(doc).name}")
    
    return source_docs


def convert_pdfs_to_docling(source_docs):
    """
    Convert PDF files to Docling documents.
    """
    logger.info("Starting PDF conversion with Docling...")
    
    # Instantiate the doc converter
    doc_converter = DocumentConverter()
    
    # Directly pass list of files to `convert_all`
    conv_results_iter = doc_converter.convert_all(source_docs)
    
    # Iterate over the generator to get a list of Docling documents
    docs = [result.document for result in conv_results_iter]
    
    logger.info(f"✓ Converted {len(docs)} documents")
    
    return docs


def chunk_documents(docs, source_docs):
    """
    Perform hierarchical chunking on documents and extract metadata.
    """
    logger.info("Starting hierarchical chunking...")
    
    # Initialize lists for text, titles, and sources
    texts = []
    titles = []
    sources = []
    
    chunker = HierarchicalChunker()
    
    # Process each document in the list
    for doc, source_path in zip(docs, source_docs):
        # Extract title from filename (remove extension and path)
        title = Path(source_path).stem
        
        # Perform hierarchical chunking
        chunks = list(chunker.chunk(doc))
        
        for chunk in chunks:
            # Concatenate title and text for better context
            chunk_text = f"{title}: {chunk.text}"
            texts.append(chunk_text)
            titles.append(title)
            sources.append(source_path)
    
    logger.info(f"✓ Created {len(texts)} chunks from {len(docs)} documents")
    
    return texts, titles, sources


def create_weaviate_collection(client, collection_name="ISODocuments"):
    """
    Create a Weaviate collection for ISO medical device documents.
    Uses OpenAI for embeddings and generation.
    """
    logger.info(f"Creating Weaviate collection: {collection_name}")
    
    # Delete the collection if it already exists
    if client.collections.exists(collection_name):
        logger.info(f"Collection '{collection_name}' already exists. Deleting...")
        client.collections.delete(collection_name)
    
    # Create the collection
    collection = client.collections.create(
        name=collection_name,
        vectorizer_config=wc.Configure.Vectorizer.text2vec_openai(
            model="text-embedding-3-large",  # OpenAI embedding model
        ),
        # Enable generative model for RAG
        generative_config=wc.Configure.Generative.openai(
            model="gpt-4o"  # OpenAI generative model
        ),
        # Define properties
        properties=[
            wc.Property(name="text", data_type=wc.DataType.TEXT),
            wc.Property(name="title", data_type=wc.DataType.TEXT, skip_vectorization=True),
            wc.Property(name="source", data_type=wc.DataType.TEXT, skip_vectorization=True),
        ],
    )
    
    logger.info(f"✓ Collection '{collection_name}' created successfully")
    
    return collection


def insert_data_to_weaviate(collection, texts, titles, sources):
    """
    Insert chunked documents into Weaviate collection.
    Embeddings will be generated automatically upon insertion.
    """
    logger.info(f"Inserting {len(texts)} chunks into Weaviate...")
    
    # Prepare data objects
    data = []
    for text, title, source in zip(texts, titles, sources):
        data_point = {
            "text": text,
            "title": title,
            "source": source,
        }
        data.append(data_point)
    
    # Insert data using batch insert
    response = collection.data.insert_many(data)
    
    if response.has_errors:
        logger.error("Errors during insertion:")
        for i, error in enumerate(response.errors):
            logger.error(f"  Error {i+1}: {error}")
        raise Exception("Failed to insert all data into Weaviate")
    else:
        logger.info(f"✓ Successfully inserted {len(data)} chunks into Weaviate")
    
    return response


def save_metadata(texts, titles, sources, output_file="iso_chunks_metadata.json"):
    """
    Save metadata about chunks to a JSON file for reference.
    """
    metadata = {
        "total_chunks": len(texts),
        "unique_documents": len(set(titles)),
        "chunks": [
            {
                "title": title,
                "source": source,
                "text_preview": text[:200] + "..." if len(text) > 200 else text
            }
            for text, title, source in zip(texts[:10], titles[:10], sources[:10])  # First 10 for preview
        ]
    }
    
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✓ Metadata saved to {output_file}")


def main():
    """
    Main function to orchestrate the entire process.
    """
    client = None
    
    try:
        # Step 1: Initialize Weaviate client
        logger.info("=" * 80)
        logger.info("STEP 1: Initializing Weaviate Client")
        logger.info("=" * 80)
        client = init_weaviate()
        
        # Step 2: Get PDF documents
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Loading PDF Documents")
        logger.info("=" * 80)
        source_docs = get_pdf_documents()
        
        # Step 3: Convert PDFs to Docling documents
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Converting PDFs with Docling")
        logger.info("=" * 80)
        docs = convert_pdfs_to_docling(source_docs)
        
        # Step 4: Chunk documents
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: Chunking Documents")
        logger.info("=" * 80)
        texts, titles, sources = chunk_documents(docs, source_docs)
        
        # Step 5: Create Weaviate collection
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: Creating Weaviate Collection")
        logger.info("=" * 80)
        collection = create_weaviate_collection(client, collection_name="ISODocuments")
        
        # Step 6: Insert data into Weaviate
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: Inserting Data into Weaviate")
        logger.info("=" * 80)
        insert_data_to_weaviate(collection, texts, titles, sources)
        
        # Step 7: Save metadata
        logger.info("\n" + "=" * 80)
        logger.info("STEP 7: Saving Metadata")
        logger.info("=" * 80)
        save_metadata(texts, titles, sources)
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("✓ PROCESS COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Total documents processed: {len(set(titles))}")
        logger.info(f"Total chunks created: {len(texts)}")
        logger.info(f"Collection name: ISODocuments")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n❌ Error occurred: {str(e)}")
        raise
    
    finally:
        # Always close the client
        if client:
            logger.info("\nClosing Weaviate client...")
            client.close()
            logger.info("✓ Client closed")


if __name__ == "__main__":
    main()
