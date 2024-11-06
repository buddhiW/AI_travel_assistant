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

def compute_travel_duration(origin, destination, mode_of_travel):
    """
    Function to compute travel duration given origin, destination and mode of travel.
    The output of this function is a string, that is used by the LLM to produce the response.
    """

    if USE_API == True:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode_of_travel,
            "key": map_api_key
        }

        errors = ''

        # Google Maps API call
        response = requests.get(url, params=params).json()
        
        origin_address = response['origin_addresses'][0]
        destination_address = response['destination_addresses'][0]

        if response['status'] == 'OK' and response['rows'][0]['elements'][0]['status'] == 'OK':
            duration = response['rows'][0]['elements'][0]['duration']['text']
            output = f'Time to travel from  {origin_address} to {destination_address} by {mode_of_travel} is {duration}.'
            return output
        elif not destination_address:
            errors + 'not enough information to determine destination address '
        elif not origin_address:
            errors + ' not enough information to determine origin address'

        return errors
    else:
        ## Time is hard-coded. In reality, this would be an API call.
        output = f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.'
        return output

def traffic_condition(origin, destination, mode_of_travel):
    """
    This function takes the origin and destination as arguments returns traffic conditions for ground travel
    """
    return f'There is heavey traffic between {origin} and {destination}, which could add 20 minutes to the journey by {mode_of_travel}'

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
map_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

USE_API = False

system_message = (
    "You are a helpful assistant that processes user queries related to travel information."
    "Answer in one sentence."
    "Follow the following routine when answering."
    "1. First, check whether the query is relevant. " 
        "Relevant questions include estimated travel duration, traffic conditions, important landmarks, places to eat. "
        "If not relevant, politely ask the user to ask a relevant question. Use two short sentences at most. \n"
    "2. Identify the type of question. \n"
    "3. If the question is about travel duration, extract origin, destination and mode of transportation from the query . \n"
    "4. If any of the information is missing, ask the user to provide the missing information. \n"
    "5. Call the travel duration computation function. \n"
    "6. If the question is about traffic condition, provide traffic condition with mode of travel as ground. \n"
    "7. For any other question, make up an answer. \n"
)

tools = [compute_travel_duration, traffic_condition]

messages = []

while True:
    user_query = input("User: ")
    messages.append({"role": "user", "content": user_query})

    result = run_assistant(system_message, messages, tools)

    messages.extend(result)






