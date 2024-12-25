"""
Author: Buddhi W
Date: 12/02/2024
AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This is a supervisor-based graph model implemented using LangGraph
All the experts are implemented as agents. Compare this with the single agent model.
Based on https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/agent_supervisor.ipynb
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

def route_tools(state:State):
    route = tools_condition(state)

    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls

    tools = [tc["name"] for tc in tool_calls]

    return tools


def build_graph():

    builder = StateGraph(State)
    
    supervisor_runnable = create_agent_runnable(supervisor_agent, structured = True)
    duration_runnable = create_agent_runnable(travel_duration_agent)
    traffic_runnable = create_agent_runnable(traffic_updates_agent)
    transit_runnable = create_agent_runnable(transit_details_agent)
    
    builder.add_node("supervisor", Supervisor(supervisor_runnable))
    builder.add_node("duration", Assistant(duration_runnable))
    builder.add_node("traffic", Assistant(traffic_runnable))
    builder.add_node("transit", Assistant(transit_runnable))

    builder.add_edge(START, "supervisor")
    # for member in members:
    #     builder.add_edge(member, "supervisor")

    ## edge from supervisor to workers
    ## tools_condition adds an edge between assistant and END
    builder.add_conditional_edges(
        "supervisor",
        lambda state:state["next"],
        path_map = ["duration", "traffic", "transit", END], ## Since we have multiple conditional edges, we need a path map for each starting node
    )

    builder.add_node("duration_tools", create_tool_node_with_fallback(travel_duration_agent.tools))
    builder.add_node("traffic_tools", create_tool_node_with_fallback(traffic_updates_agent.tools))
    builder.add_node("transit_tools", create_tool_node_with_fallback(transit_details_agent.tools))

    ## Connecting tool nodes and workers
    builder.add_conditional_edges(
        "duration",
        tools_condition,
        path_map=["duration_tools"],
    )
    builder.add_conditional_edges(
        "traffic",
        tools_condition,
        path_map = ["traffic_tools"],
    )
    builder.add_conditional_edges(
        "transit",
        tools_condition,
        path_map = ["transit_tools"],
    )

    builder.add_edge("duration_tools", "duration")
    builder.add_edge("traffic_tools", "traffic")
    builder.add_edge("transit_tools", "transit")

    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)

    return graph

graph = build_graph()
graph.get_graph().draw_mermaid_png(output_file_path="my_graph_5.png")

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


messages = []

## Creating a unique ID and configuration
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id},}

graph = build_graph()

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


