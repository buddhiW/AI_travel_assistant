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
Date: 12/02/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This is a supervisor-based graph model implemented using LangGraph
All the experts are implemented as agents. Compare this with the single agent model.
"""

import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from agents import *
from utils import *
from tools import *

def create_branch(builder, agent:Agent, task_name:str):

    #builder = StateGraph(state)
    agent_runnable = create_agent_runnable(agent)

    entry_node_name = "enter_" + task_name
    tools_node_name = task_name + "_tools"

    builder.add_node(entry_node_name, create_entry_node(task_name + "_assistant", task_name))
    builder.add_node(task_name, Assistant(agent_runnable))
    builder.add_node(tools_node_name, create_tool_node_with_fallback(agent.tools + [transfer_back_to_triage_agent]))

    builder.add_edge(entry_node_name, task_name)
    builder.add_conditional_edges(
        task_name,
        route_tools,
        path_map = [tools_node_name, "leave_skill", END],
    )
    builder.add_edge(tools_node_name, task_name)

    #return builder
    

def build_graph():

    builder = StateGraph(State)

    create_branch(builder, travel_duration_agent, "travel_duration")  
    create_branch(builder, traffic_updates_agent, "traffic_updates")  
    create_branch(builder, transit_details_agent, "transit_details")  

    triage_runnable = create_agent_runnable(triage_agent)



    # duration_runnable = create_agent_runnable(travel_duration_agent)
    # traffic_runnable = create_agent_runnable(traffic_updates_agent)
    # transit_runnable = create_agent_runnable(transit_details_agent)
    
    # builder.add_node("enter_travel_duration", create_entry_node("travel duration assistant", "duration"))
    # builder.add_node("enter_traffic_updates", create_entry_node("traffic updates assistant", "traffic"))
    # builder.add_node("enter_transit_details", create_entry_node("transit schedule assistant", "transit"))

    # builder.add_node("duration", Assistant(duration_runnable))
    # builder.add_node("traffic", Assistant(traffic_runnable))
    # builder.add_node("transit", Assistant(transit_runnable))

    # builder.add_node("duration_tools", create_tool_node_with_fallback(travel_duration_agent.tools + [transfer_back_to_triage_agent])) ## Since transfer_back_to_triage_agent is not a StructuredTool, add is separately.
    # builder.add_node("traffic_tools", create_tool_node_with_fallback(traffic_updates_agent.tools + [transfer_back_to_triage_agent]))
    # builder.add_node("transit_tools", create_tool_node_with_fallback(transit_details_agent.tools + [transfer_back_to_triage_agent]))

    # builder.add_edge("enter_travel_duration", "duration")
    # builder.add_edge("enter_traffic_updates", "traffic")
    # builder.add_edge("enter_transit_details", "transit")

    # ## Connecting tool nodes and workers
    # builder.add_conditional_edges(
    #     "duration",
    #     route_tools,   ######### MAY BE WE SHOULD USE A CUSTOM ROUTE INSTEAD OF TOOLS_CONDITION ITSELF? THE PROBLEM IS GOING FROM DURATION TO THE TOOL.
    #     path_map=["duration_tools", "leave_skill", END],
    # )
    # builder.add_conditional_edges(
    #     "traffic",
    #     route_tools,
    #     path_map = ["traffic_tools", "leave_skill", END],
    # )
    # builder.add_conditional_edges(
    #     "transit",
    #     route_tools,
    #     path_map = ["transit_tools", "leave_skill", END],
    # )

    # builder.add_edge("duration_tools", "duration")
    # builder.add_edge("traffic_tools", "traffic")
    # builder.add_edge("transit_tools", "transit")


    ## Designing the triage assistant
    builder.add_node("triage", Assistant(triage_runnable))
    builder.add_edge(START, "triage")

    builder.add_node("leave_skill", return_control)
    builder.add_edge("leave_skill", "triage")
    # for member in members:
    #     builder.add_edge(member, "triage")

    ## edges from triage to workers
    builder.add_conditional_edges(
        "triage",
        route_triage_assistant,
        path_map = ["enter_travel_duration", "enter_traffic_updates", "enter_transit_details", END], ## Since we have multiple conditional edges, we need a path map for each starting node
    )


    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph

# graph = build_graph()
# graph.get_graph().draw_mermaid_png(output_file_path="my_graph_8.png")

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

messages = []

## Creating a unique ID and configuration
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id},}

graph = build_graph()
#graph.get_graph().draw_mermaid_png(output_file_path="my_graph_8.png")

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


