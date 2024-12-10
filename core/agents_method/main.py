"""
This file includes codes adapted from https://cookbook.openai.com/examples/orchestrating_agents?utm_source=www.therundown.ai&utm_medium=newsletter&utm_campaign=anthropic-ceo-predicts-ai-utopia&_bhlid=db30852b7747db2f62cd8fde276efcf151c6c21a

MIT License

Copyright (c) 2023 OpenAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Author: Buddhi W
Date: 11/5/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This implementation is purely based on OpenAI API, without other libraries such as LangChain and LangGraph.

"""

from openai import OpenAI
import openai
import requests
from dotenv import load_dotenv
import os
from pydantic import BaseModel
from typing import Optional

from utils import execute_tool_call, function_to_schema
from agents import *


class Response(BaseModel):
    agent: Optional[Agent]
    messages: list

def run_assistant(agent, messages):

    """
    Run the AI assistant pipeline.

    Parameters:
    agent (Agent): The current agent that controls the application.
    messages (list): Input obtained through stdin.

    Returns:
    str: Output displayed on stdout.
    """
    
    current_agent = agent
    num_init_messages = len(messages)
    messages = messages.copy()

    while True:

        ## Convert Python functions to schemas
        tool_schemas = [function_to_schema(tool) for tool in current_agent.tools]
        tool_map = {tool.__name__: tool for tool in current_agent.tools}

        ## Get chat completion
        response = client.chat.completions.create(
            model= current_agent.model,
            messages=[{"role": "system", "content": current_agent.instructions}] + messages,
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
            result = execute_tool_call(tool_call, tool_map, current_agent.name)

            if type(result) == Agent:
                current_agent = result
                result = (
                    f'Transfered to {current_agent.name}. Adopt persona immediately.'
                )

            result_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }

            messages.append(result_message)
    
    ## Return recent messages
    return Response(agent=current_agent, messages=messages[num_init_messages:])


load_dotenv()

## If you want LangSmith to trace your runs, set this environmental variable
#os.environ["LANGCHAIN_TRACING_V2"] = "true"

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
map_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

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

messages = []
agent = triage_Agent
while True:
    user_query = input("User: ")
    messages.append({"role": "user", "content": user_query})

    response = run_assistant(agent, messages)
    agent = response.agent
    messages.extend(response.messages)

