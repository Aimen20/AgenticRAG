from utils import api_key, client, embedding_model_name
from utils.config import data_ingestion_conf
from utils.utilities import upload_data_to_qdrant
from qdrant_client.models import VectorParams, Distance

file_path = 'Product_Data.csv'

client.create_collection(
    collection_name="products",
    vectors_config={
        "image": VectorParams(
            size=512,   # image embedding size
            distance=Distance.COSINE
        ),
        "text-dense": VectorParams(
            size=3072,   # text embedding size
            distance=Distance.COSINE
        ),
    }
)
# Set up the configuration for data ingestion
text_embed_model, image_embed_model = data_ingestion_conf(api_key= api_key,
                                                          embedding_model_name = embedding_model_name)
# Upload the data to Qdrant
upload_data_to_qdrant(client = client, 
                      text_embedding = text_embed_model,
                      image_embedding = image_embed_model,
                      file_path = file_path)



