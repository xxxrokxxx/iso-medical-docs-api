import os
import weaviate
from weaviate.classes.init import Auth
from weaviate.agents.query import QueryAgent
from weaviate_agents.classes import QueryAgentCollectionConfig
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

 # Get environment variables
voyageai_key = os.getenv("VOYAGEAI_APIKEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

headers = {
            "X-VoyageAI-Api-Key": voyageai_key,
            "X-Openai-Api-Key": openai_api_key,
        }

client = weaviate.connect_to_weaviate_cloud(
  cluster_url=weaviate_url,
  auth_credentials=Auth.api_key(weaviate_api_key),
  headers=headers
)



agent = QueryAgent(
  client=client,
  collections=[
    QueryAgentCollectionConfig(
      name="ISODocuments",
    ),
  ],
)

query = """What is a key for a software to be labeled as non critical medical device?"""

result = agent.run(query)
print(result)