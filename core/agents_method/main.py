"""
Author: Buddhi W
Date: 11/5/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This implementation is based on https://cookbook.openai.com/examples/orchestrating_agents?utm_source=www.therundown.ai&utm_medium=newsletter&utm_campaign=anthropic-ceo-predicts-ai-utopia&_bhlid=db30852b7747db2f62cd8fde276efcf151c6c21a
"""

from openai import OpenAI
import openai
import requests
from dotenv import load_dotenv
import os

from utils import execute_tool_call, function_to_schema
from agents import *

def run_assistant(agent, messages):

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
    tool_schemas = [function_to_schema(tool) for tool in agent.tools]
    tool_map = {tool.__name__: tool for tool in agent.tools}

    while True:

        ## Get chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": agent.instructions}] + messages,
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


messages = []
user_query = "How much time will it take for me to go from Colombo to Kandy by bus?"
print("User: ", user_query)
messages.append({"role": "user", "content": user_query})

response = run_assistant(travel_duration_agent, messages)
messages.extend(response)

user_query = "How is the traffic situation on this route?"
print("User: ", user_query)
messages.append({"role": "user", "content": user_query})

response = run_assistant(traffic_condition_agent, messages)
messages.extend(response)

user_query = "Can you find me the bus schedule for this route?"
print("User: ", user_query)
messages.append({"role": "user", "content": user_query})
response = run_assistant(transit_schedule_agent, messages)


