
import re
import json
from utils import *
from utils.config import text_to_image_conf
from utils.prompts import *
import chainlit as cl
import asyncio
import random
from llama_index.core import Settings
from llama_index.core.llms import ChatMessage, ImageBlock, TextBlock

text_embed_model, image_embed_model = text_to_image_conf(api_key = api_key,
                                                         model_name = model_name,
                                                        embedding_model_name = embedding_model_name)

async def qualified_products(results, price: float = None):
    """
    This function performs manipulation on the results fetched from Vector Store
    Parameters:
    - results: The meta data of the embeddings fetched from vector store
    - price (float): The maximum price for filtering products.
    Returns:
    - json_file (dict): A dictionary containing matched products and similar products.
    """
    # Filter results based on a confidence threshold (e.g., 0.75)

    similar_products = [res for res in results.points if res.score >= 0.75]

    # Filter results based on price if price is provided
    final_results = []
    if price is not None:
        final_results = [res for res in similar_products if float(res.payload.get('price')) <= price]
        similar_products = [res for res in similar_products if not res.id in [final_res.id for final_res in final_results]]

    json_file =[]
    matched_products =[]
    similar_products_but_higher_price = []

    for prod in final_results:
        product_info = {
            'title': prod.payload.get('title'),
            'description': prod.payload.get('description'),
            'price': prod.payload.get('price'),
            'currency': prod.payload.get('currency'),
            'imageUrl': prod.payload.get('imageUrl')
        }
        matched_products.append(product_info)
    
    for prod in similar_products:
        product_info = {
            'User_specified_price': True if price is not None else False,
            'title': prod.payload.get('title'),
            'description': prod.payload.get('description'),
            'price': prod.payload.get('price'),
            'currency': prod.payload.get('currency'),
            'imageUrl': prod.payload.get('imageUrl')
        }
        similar_products_but_higher_price.append(product_info)

    json_file = {
         'matched_products': matched_products,
         'similar_products_but_higher_price': similar_products_but_higher_price
    }

    if matched_products or similar_products_but_higher_price:
        json_file = {
            'matched_products': matched_products,
            'similar_products_but_higher_price': similar_products_but_higher_price
         }
    else:
        json_file = {
            "matched_products": [],
            "similar_products_but_higher_price": [],
            "title": "No products found",
            "description": "No products were found in the database for this specific search."
                
        }
 
    return json_file


async def query_vector_Store(vector_config: str, query_vector, top_k: int = 3):
    """
    This function queries the vector store collection 'products' and returns the results
    Parameters:
    - vector_config (str): Name of vector config
    - query_vector: Query embeddings to run on vector_config
    - top_k (int): The number of top results to retrieve
    Returns:
    - Results: Similar results fetched from vector_config based on query_vector and top_k

    """

    results = client.query_points(
            collection_name="products",
            query=query_vector,   
            using=vector_config,   
            limit=top_k
        )
    
    return results

async def multi_modal_search(user_query: str, price: float = None, top_k: int = 3):

    """
    This function searches products while matching the image and textual prompt of the user and
    filters based on price and confidence level
    Parameters:
    - user_query (str): The search query input by the user.
    - price (float): The maximum price for filtering products.
    - top_k (int): The number of top results to retrieve.
    Returns:
    - json_file (dict): A dictionary containing matched and similar products.
    """
    image_path = cl.user_session.get('image_path')
    if image_path:

        fusion_prompt = f"""
            Compare the user's request with the provided image.
            User Request: {user_query}

            Instructions:
            1. Identify the product in the image.
            2. Apply the modifications requested by the user (e.g., color, material, style).
            3. Output a single, highly descriptive search string for a product database.
            4. Focus on technical attributes like 'material', 'color', 'shape', and 'category'.
            """
        image_block = ImageBlock(path=image_path)
        
        message = ChatMessage(
        role="user",
        content=[
            TextBlock(text=fusion_prompt),
            image_block
        ] )
        # Generate a response for the text embedding that captures the image and textual prompt
        response = await Settings.llm.achat([message])
        
        print(f"UPDATED QUERY: {response.message.content}")
        query_vector = text_embed_model.get_text_embedding(response.message.content)

        text_results = await query_vector_Store(vector_config="text-dense",
                           query_vector=query_vector,
                           top_k=top_k)
        
        json_file = await qualified_products(results = text_results,
                                            price = price)
       
        cl.user_session.set('image_path', None)
    else:
        json_file= {
            "matached_products": [],
            "similar_products_but_higher_price": [],
            "title": "No Image found",
            "description": "Please attach the Image to proceed"
                
        }
    return json_file


async def search_image_with_text(price: float = None, top_k: int = 3):

    """
    This function searches products while matching the image uploaded by the user and
    filters based on price and confidence level
    Parameters:
    - price (float): The maximum price for filtering products.
    - top_k (int): The number of top results to retrieve.
    Returns:
    - json_file (dict): A dictionary containing matched and similar products.
    """
    image_path = cl.user_session.get('image_path')
    if image_path:
        image_vec = image_embed_model.get_image_embedding(image_path)

        results_img = await query_vector_Store(vector_config="image",
                           query_vector=image_vec,
                           top_k=top_k)
        
        json_file = await qualified_products(results= results_img,
                                            price = price)
        # Clear the image set in user session
        cl.user_session.set('image_path', None)
    else:
        json_file= {
            "matached_products": [],
            "similar_products_but_higher_price": [],
            "title": "No Image found",
            "description": "Please attach the Image to proceed"
                
        }
    return json_file


async def search_text_with_image(user_query: str, price: float = None, top_k: int = 3):
    """
    This function searches for products based on a user query and filters based on price and confidence level
    Parameters:
    - user_query (str): The search query input by the user.
    - price (float): The maximum price for filtering products.
    - top_k (int): The number of top results to retrieve.
    Returns:
    - json_file (dict): A dictionary containing matched and similar products.
    """

    query_vector = text_embed_model.get_text_embedding(user_query)

    text_results = await query_vector_Store(vector_config="text-dense",
                           query_vector=query_vector,
                           top_k=top_k)
   
    json_file = await qualified_products(results = text_results,
                                         price = price)

    return json_file

async def display_results_on_UI(message : str):
    """
    This function sends a streaming message to the chat interface with the agent's response. 
    """
    msg = cl.Message(content="", author = "logo")
    await msg.send()

    pattern = r'!\[(.*?)\]\((.*?)\)'
    parts = re.split(pattern, message)
    
    chunk_size = random.randint(5, 10)

    i=0
    while i < len(parts):

        # TEXT PART
        text = parts[i]
        if text and i!=0:
            msg = cl.Message(content="", author = "logo")
            # Create a new message
            await msg.send()

        #  Stream text to message
        for j in range(0, len(text), chunk_size):
            chunk = text[j:j+chunk_size]
            await msg.stream_token(chunk)
            await asyncio.sleep(random.uniform(0.05, 0.07))

        # Finalize the buffered text on UI
        await msg.update()

        # Send image 
        if i + 2 < len(parts):
            alt = parts[i+1]
            url = parts[i+2]

            #  Send a new message as an image
            await cl.Message(
                content="",
                elements=[cl.Image(url=url, name=alt, display="inline")], 
                author = "logo"
            ).send()

        i += 3


async def update_history(role:str, content:str):
    """
    This function updates the history of messages
    """
    history = cl.user_session.get("history")
    history.append({
            "role": role,
            "content": content})

    cl.user_session.set("history", history)


async def agent_execution(message: str):
    """
    This function executes the agent's response to the user's message, 
    including handling tool calls and displaying results on the UI.
    """

    agent = cl.user_session.get("agent")
    history = cl.user_session.get("history")
    pending_products = cl.user_session.get('pending_products')

    if pending_products:
        prompt = f"""
                Determine the user's intention.

                User message: "{message}"

                Possible intents:
                - AGREE
                - DISAGREE
                - UNCLEAR

                Respond with ONLY one word: AGREE, DISAGREE, or UNCLEAR.
                """
        response = await agent.llm.acomplete(prompt)

        intent = response.text.strip()

        if intent == 'AGREE':

            products_json = json.dumps(pending_products, indent=2)
            similar_products_prompt = f"""
                Only recommend the products in {products_json} to the user.
                Do not call any tool

                DISPLAY: For each Product, show title and describe the specifications 
                (description, price with currency) in a natural tone.
                Display the product image as well.
                Display according to following instructions:
                - Use ### before the product title to make it stand out. Add a bullet point to start of each product listing.
                - Describe the product in a natural and engaging way along with price, as if you are recommending it to a client.
                - Use new line spacing between product description and image.
                - Use double line spacing between listing different products to make it visually appealing. 
                """
            
            handler = agent.run(user_msg = similar_products_prompt,
                        chat_history = history)
        else:

            #  The user says no

            handler = agent.run(user_msg = message,
                        chat_history = history)

        # Wait for final response
        response = await handler
        
        cl.user_session.set('pending_products', None)


    else:  
        # 1. Ask the Agent to think and call the tool
        handler = agent.run(user_msg = message,
                        chat_history = history)
        # Wait for final response
        response = await handler

        is_function_call = len(response.tool_calls) > 0

        if not is_function_call:
            image_path = cl.user_session.get('image_path')
            if image_path:

                # 1. Ask the Agent to think and call the tool
                handler = agent.run(user_msg = user_upload_image_message,
                                chat_history = history)
                # Wait for final response
                response = await handler
            else:

                print("No function call detected. Agent response: ", response)

        
        else:
            print("Function call detected. Tool calls: ", response.tool_calls[0])
            tool_call_result = response.tool_calls[0]
            
            products = tool_call_result.tool_output.raw_output
           

            if len(products['similar_products_but_higher_price']) > 0:
                # Confirm the user, if interested in similar but higher priced products
                if products['similar_products_but_higher_price'][0].get("User_specified_price"):
                    
                    handler = agent.run(user_msg = confirmation_prompt,
                        chat_history = history)
                    
                    
                    # Wait for final response
                    response = await handler
                    
                    
                    cl.user_session.set('pending_products', products['similar_products_but_higher_price'] )

                    
                else:
                # User has not specified the price, display the similar products directly without confirmation
                    products_json = json.dumps(products['similar_products_but_higher_price'], indent=2)
                    similar_products_prompt = f"""
                        Only recommend the products in {products_json} to the user.
                        Do not call any tool

                        DISPLAY: For each Product, show title,
                        description and price with currency in a natural tone.
                        Display the product image as well.
                        Display according to following instructions:
                        - Use ### before the product title to make it stand out. Add a bullet point to start of each product listing.
                        - Describe the product in a natural and engaging way along with price, as if you are recommending it to a client.
                        - Use new line spacing between product description and image.
                        - Use double line spacing between listing different products to make it visually appealing. 
                        """
                    
                    handler = agent.run(user_msg = similar_products_prompt,
                        chat_history = history)
                     # Wait for final response
                    response = await handler
                    

    # Display response on UI
    await display_results_on_UI(message = str(response))

    # Append history of agent response
    await update_history(role = "assistant",
                    content = str(response))
    print('History')
    print(history)

        