from llama_index.core import Settings
from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.clip import ClipEmbedding



def data_ingestion_conf(api_key, embedding_model_name):

    """
    This function configures the embedding model required for data ingestion.
    Parameters:
    - api_key (str): The API key for accessing the Google GenAI embedding model.
    - embedding_model_name (str): The name of the embedding model to use.
    """
    # # No need for LLM in Data ingestion
    Settings.llm = None

    # Use the available embedding model
    text_embed_model = GoogleGenAIEmbedding(model_name=f"models/{embedding_model_name}",
                                            api_key=api_key)

    image_embed_model = ClipEmbedding()

    #  Embedding model necessary to calculate vectors
    Settings.embed_model = text_embed_model

    return text_embed_model, image_embed_model
                                       

def text_to_image_conf(api_key, model_name, embedding_model_name):

    """
    This function configures the LLM and embedding model required for the query engine.
    Parameters:
    - api_key (str): The API key for accessing the Google Gemini models.
    - model_name (str): The name of the LLM to use.
    - embedding_model_name (str): The name of the embedding model to use.
    """
    # Required LLM for generating the final response to the user
    Settings.llm = Gemini(model_name=f"models/{model_name}",
                          api_key=api_key)

    text_embed_model = GoogleGenAIEmbedding(model_name=f"models/{embedding_model_name}",
                                                api_key=api_key)

    image_embed_model = ClipEmbedding()

    #  Embedding model necessary to calculate vectors for user response
    Settings.embed_model = text_embed_model

    return text_embed_model, image_embed_model
    


