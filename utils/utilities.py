
import pandas as pd
import requests
from io import BytesIO
from qdrant_client.http.models import PointStruct
import uuid


def data_preprocessing(file_path):
    """
    This function reads the CSV file and performs basic preprocessing steps.
    Parameters:
    - file_path: The path to the CSV file containing the product data.
    Returns:
    - Dataframe: Processed Panda Dataframe 
    """
    df = pd.read_csv(file_path)

    # Replace NaN in numeric columns with 0
    df['price'] = df['price'].fillna(0.0)

    # Replace NaN in categories with 'General'
    df['categories'] = df['categories'].fillna("General")

    # Drop Rows with NAN images and descriptions
    df = df.dropna(subset=['imageUrl'])
    df = df.dropna(subset=['description'])
    df = df.dropna(subset=['title'])

    return df

def load_image_from_url(url):
    """
    This function returns the images bytes from URL
    Parameters:
    - url: Image url
    Returns:
    - BytesIO: Image object in bytes
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        image = BytesIO(response.content)
    except:
        print(f"Failed to fetch image: {url}")
        image = 'Error'

    return image
        
def upload_data_to_qdrant(client, text_embedding, image_embedding, file_path):
    """
    This function reads the file (CSV) and uploads the data to the Qdrant collection
    Parameters:
    - client: The Qdrant client instance used to interact with the Qdrant collection.
    - text_embedding: The embedding model used to generate text embeddings for the product descriptions.
    - image_embedding: The embedding model used to generate image embeddings for the product images.
    - file_path: The path to the CSV file containing the product data.
    """
    namespace = uuid.NAMESPACE_DNS

    df = data_preprocessing(file_path)
    print(len(df))
    points = []

    for i, row in df.iterrows():
        
        # load the image
        image = load_image_from_url(row['imageUrl'])
        if image == 'Error':
            continue

        # Get the text and image embeddings
        image_vec = image_embedding.get_image_embedding(image)
        text_content = f"{row['title']}. {row['description']}"
        text_vec = text_embedding.get_text_embedding(text_content)
        
        # Assign Meta data to Text and Image Point
        metadata = {
        "title": row["title"],
        "price": row["price"],
        "category": row["categories"],
        "currency": row["currency"],
        "product_id": row["asin"],
        "imageUrl": row["imageUrl"],
        "description": row["description"]
    }
        id = str(uuid.uuid5(namespace, row["asin"]))

        point = PointStruct(
            id= id,
            vector={
                "text-dense": text_vec,
                "image": image_vec
            },
            payload=metadata
        )

        points.append(point)
    
    try:
        
        client.upload_points(collection_name="products",
                points=points)

        print('Successfully Uploaded')
    except Exception as e:
        print(f'Upload error {e}')
