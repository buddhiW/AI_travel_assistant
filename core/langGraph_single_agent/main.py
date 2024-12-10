"""
This file includes codes adapted from https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/

MIT License

Copyright (c) 2024 LangChain, Inc.

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
Date: 11/22/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This implementation is a graph-based model implemented using LangGraph

"""
import uuid
import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from agents import State, Assistant, triage_agent
from utils import create_tool_node_with_fallback

def build_graph(agent):

    builder = StateGraph(State)
    llm = ChatOpenAI(temperature = 0.7, model=agent.model)
    tools = agent.tools
    primary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", agent.instructions,),
            ("placeholder", "{messages}",)
        ]
    )  
    assistant_runnable = primary_prompt | llm.bind_tools(tools)

    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_node("tools", create_tool_node_with_fallback(tools))
    builder.add_edge(START, "assistant")
    ## edge from assistant to tools
    ## tools_condition adds an edge between assistant and END
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
    )
    ## edge from tools to assistant
    builder.add_edge("tools", "assistant")

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph

#graph = build_graph(triage_agent)
#graph.get_graph().draw_mermaid_png(output_file_path="my_graph.png")

def run_assistant(config, graph, question):

    """
    Run the AI assistant pipeline.

    Parameters:
    agent (Agent): The current agent that controls the application.
    messages (list): Input obtained through stdin.

    Returns:
    str: Output displayed on stdout.
    """

    events = graph.stream(
        {"messages": ("user", question)}, config, stream_mode="values"
    )
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()
            snapshot = graph.get_state(config)
            print(snapshot.next)
    
    ## Return recent messages
    #return Response(agent=current_agent, messages=messages[num_init_messages:])

## If you want LangSmith to trace your runs, set this environmental variable
#os.environ["LANGCHAIN_TRACING_V2"] = "true"

messages = []

## Creating a unique ID and configuration
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id},}

graph = build_graph(triage_agent)

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


## We don't have to append messages to a list because we use MemorySaver() to maintain memory
while True:
    user_query = input("User: ")
    run_assistant(config, graph, user_query)



