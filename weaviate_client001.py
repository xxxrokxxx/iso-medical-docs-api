import os
import weaviate
from weaviate.classes.init import Auth
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def init_weaviate():
    '''
    Initialize and return a Weaviate client.
    '''
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

        logger.info(f"Connecting to Weaviate at: {wcd_url}")
        logger.info(f"VoyageAI API Key available: Yes")
        logger.info(f"OpenAI API Key available: Yes")

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=wcd_url,
            auth_credentials=Auth.api_key(wcd_api_key),
            headers=headers
        )

        # Check if the client is ready
        try:
            if client.is_ready():
                logger.info("Weaviate connection successful! Client is ready.")
            else:
                logger.warning("WARNING: Weaviate client connected but reports not ready.")
        except Exception as e:
            logger.warning(f"Could not check client readiness: {str(e)}")

        return client

    except Exception as e:
        logger.error(f"Error initializing Weaviate: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        client = init_weaviate()
        print(f"Client is ready: {client.is_ready()}")
    finally:
        if 'client' in locals():
            client.close()