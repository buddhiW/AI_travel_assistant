"""
Author: Buddhi W
Date: 07/25/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This implementation is based on https://cookbook.openai.com/examples/orchestrating_agents?utm_source=www.therundown.ai&utm_medium=newsletter&utm_campaign=anthropic-ceo-predicts-ai-utopia&_bhlid=db30852b7747db2f62cd8fde276efcf151c6c21a
"""

from openai import OpenAI
import openai
import requests
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from utils import execute_tool_call, function_to_schema
from tools import *

def run_assistant(system_message, messages, tools):

    """
    Run the AI assistant pipeline.

    Parameters:
    user_query (str): Input obtained through web UI.

    Returns:
    str: Output displayed on the web UI.
    """
    
    num_init_messages = len(messages)
    messages = messages.copy()

    ## Convert Python functions to schemas
    tool_schemas = [function_to_schema(tool) for tool in tools]
    tool_map = {tool.__name__: tool for tool in tools}

    while True:

        ## Get chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_message}] + messages,
            tools= tool_schemas or None,
        )

        message = response.choices[0].message
        messages.append(message)

        if message.content:
            print("Assistant:", message.content)
        
        if not message.tool_calls:
            break

        ## Execute tool calls (if any)
        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tool_map)

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }

            messages.append(result_message)
    
    ## Return recent messages
    return messages[num_init_messages:]


load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

USE_API = False

system_message = (
    "You are a helpful assistant that processes user queries related to travel information."
    "Answer in one sentence."
    "Follow the following routine when answering."
    "1. First, check whether the query is relevant. " 
        "Relevant questions include estimated travel duration, traffic conditions, transit route information, transit route schedules, important landmarks, places to eat. "
        "If not relevant, politely ask the user to ask a relevant question. Use two short sentences at most. \n"
    "2. Identify the type of question. \n"
    "3. For questions related to travel duration, traffic conditions, transit route information, transit route schedules, call the relevant function. \n"
    "4. If any of the information for the function call is missing, ask the user to provide the missing information. \n"
    "5. For any other questions, make up an answer. \n"
)

questions = [
    "How much time will it take me to go from Sunnyvale to Mountain View by car?",
    "How is the traffic situation on this route?",
    "How long will it make for me to cycle to Golden Gate Bridge?",
    "What is the travel time between Eureka, Mountain View and Caltrain Station, Mountain View?",
    "Which bus route should I take for this trip?",
    "I changed my mind. What is the best train route?",
    "Can you give me the train schedule for this route?",
    "Can you recommend a good place to dine in San Francisco?",
    "How much time will it take to drive from there to Golden Gate Park?",
]

tools = [compute_travel_duration, traffic_condition, find_route, find_transit_schedule]

messages = []

while True:
    user_query = input("User: ")
    messages.append({"role": "user", "content": user_query})

    result = run_assistant(system_message, messages, tools)

    messages.extend(result)






