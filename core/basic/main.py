"""
Author: Buddhi W
Date: 07/25/2024
Functions related to AI assistant that computes current travel distance between two locations for a given mode of travel.
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
    """
    ## Time is hard-coded. In reality, this would be an API call.
    #print(f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.')
    output = f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.'
    return output

# Creat tools (functions) for each case and let the model decide which function to call.
#     Make the system prompt more detailed with steps -> ask what to do in each case within the steps.



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

system_message = (
    "You are a helpful assistant that processes user queries related to travel duration computation."
    "Answer in one sentence."
    "Follow the following routine when answering."
    "1. First, check whether the query is relevant. If not, politely ask the user to ask a relevant question. \n"
    "2. Extract origin, destination and mode of transportation from the query. \n"
    "3. If any of the information is missing, ask the user to provide the missing information. \n"
    "4. Call the travel duration computation function. \n"
    "5. If done, conclude the conversation."
)

tools = [compute_travel_duration]

messages = []

while True:
    user_query = input("User: ")
    messages.append({"role": "user", "content": user_query})

    result = run_assistant(system_message, messages, tools)

    messages.extend(result)






