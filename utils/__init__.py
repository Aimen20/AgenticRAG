import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient


# Load credentials
load_dotenv()

# Get Credentials
qdrant_url =  os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
api_key = os.getenv("GOOGLE_API_KEY")
model_name = os.getenv("MODEL_NAME")
embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME")

# # Initialize Qdrant Client
client = QdrantClient(url=qdrant_url,
                       api_key=qdrant_api_key,
                       timeout=60)
