import chainlit as cl
from utils.prompts import system_prompt
from utils.functions import *
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core import Settings


@cl.on_chat_start
async def on_chat_start():

    # Wrap the functions as a LlamaIndex Tool
    text_with_image_tool = FunctionTool.from_defaults(fn=search_text_with_image,
                                              name = 'search_text_with_image',
                                              description= 'Searches products using text for similarity and filtering results')
    
    image_with_text_tool = FunctionTool.from_defaults(fn=search_image_with_text,
                                              name = 'search_image_with_text',
                                              description= 'Searches products using image for similarity and text for filtering results')
    
    multi_modal_search_tool = FunctionTool.from_defaults(fn=multi_modal_search,
                                                         name = 'multi_modal_search',
                                                         description='Searches products using text and image for similarity and further filter results')
    
    product_tools = [text_with_image_tool,
                    image_with_text_tool,
                    multi_modal_search_tool]

    # Initialize the agent
    agent = FunctionAgent(
        name= "Product Recommendation Agent",
        description="""An agent that searches for products 
        based on user queries and returns relevant product information""",
        tools=product_tools,
        llm=Settings.llm,
        system_prompt=system_prompt,
        verbose=True,
        streaming= True
    )

    # Initialize user session
    cl.user_session.set("history", [])
    # Store the agent in the user session
    cl.user_session.set("agent", agent)


    await cl.Message(
        content="Welcome to the chat! How can I assist you today?",
        author = "logo"
    ).send()



@cl.on_message
async def main(message: cl.Message):

    content = message.content

    # If user has attached an image file
    for element in message.elements:
        if element.mime.startswith("image/") and element.name.lower().endswith((".png", ".jpg", ".jpeg")):
            print('image detected')
            if (element.path):
                cl.user_session.set('image_path', element.path)
                content+= "\n[User uploaded an image]"
        else:
            await display_results_on_UI(message = "Please upload a valid image. Only PNG and JPG are accepted")

            return

    # Update history
    await update_history(role = "user",
                         content= content)
    
    # # Run the agent execution for the user's message
    await agent_execution(message = message.content)
