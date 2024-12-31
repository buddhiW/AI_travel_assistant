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
Date: 12/27/2024
Implementations of agents and related functions.

"""
from typing import Annotated, Literal, Callable
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

from pydantic import BaseModel

from tools import *

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next:str

## We use this to force supervisor node to generate a structured output
class Router(TypedDict):
    next:str

## This general agent class can be used to define various agents, including an assistant agent.
## Note that langgraph has a prebuilt agent that can be created through create_react_agent(). 
## However, creating our own agents offers better flexibility.
class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "Your are a helpful Agent"
    tools: list = []

class Supervisor:

    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state:State):

        result = self.runnable.invoke(state)
        next_ = result["next"]

        return {"next": next_}

## Executing the runnable assistant agent
class Assistant:

    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State):

        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break

        return {"messages": result}


def create_agent_runnable(agent:Agent, structured:bool = False):

    llm = ChatOpenAI(temperature = 0.7, model=agent.model)
    if structured:
        llm = llm.with_structured_output(Router)

    tools = agent.tools
    primary_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", agent.instructions,),
            ("placeholder", "{messages}",)
        ]
    )  

    if tools:
        assistant_runnable = primary_prompt | llm.bind_tools(tools)
    else:
        assistant_runnable = primary_prompt | llm

    return assistant_runnable

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. "
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the triage assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
        }

    return entry_node

## Supervising agent that calls the tools as it sees fit.
triage_agent = Agent(
    name = "triage agent",
    instructions = "You are a helpful assistant that helps users plan trips and travels by providing useful information. "
                    "If a customer requests information on travel duration, traffic conditions, transit route or transit schedule, "
                    "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. "
                    "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
                    "For any other travel related questions, make up an informative answer. Answer in at most two sentences. "
                    "Allow questions that are tangential, as long as they fulfill the goal of providing information related to travelling."
                    "If the query is not relevant, politely ask the user to ask relevant questions. ",
    tools = [transfer_to_travel_duration_agent,
             transfer_to_traffic_updates_agent,
             transfer_to_transit_details_agent,],
)
    
travel_duration_agent = Agent(
    name = "travel duration agent",
    instructions= "Your are an agent that computes travel duration using origin, destination and travel mode. "
                    "If the user needs help, and none of your tools are appropriate for it, then "
                    '"transfer_back_to_triage_agent". Do not make up answers or invalid tools. ',
    tools= [compute_travel_duration,],
)

traffic_updates_agent = Agent(
    name = "traffic condition agent",
    instructions = "You are an agent that provides real-time traffic updates for a route. "
                    "If the user needs help, and none of your tools are appropriate for it, then "
                    '"transfer_back_to_triage_agent". Do not make up answers or invalid tools. ',
    tools = [traffic_condition,],
)

# transit_route_agent = Agent(
#     name = "transit route agent",
#     instructions = "You are an agent that provides the transit route (bus, train, tram) given origin, destination. "
#                     "If the mode of travel is not transit, that is bus, train, tram, ask the user to input a valid mode of travel. "
#                     "If the user needs help, and none of your tools are appropriate for it, then "
#                        '"transfer_back_to_triage_agent". Do not make up answers or invalid tools. ',
#     tools = [find_route,],
# )

## Combined two agents into one.
transit_details_agent = Agent(
    name = "transit details agent",
    instructions = "You are an agent that provides information related to transit (bus, train, tram) routes and schedules, given origin, destination. "
                    "If the mode of travel is not transit, that is bus, train, tram, ask the user to input a valid mode of travel. "
                    "If the user needs help, and none of your tools are appropriate for it, then "
                    '"transfer_back_to_triage_agent". Do not make up answers or invalid tools. ',
    tools = [find_route, find_transit_schedule,],
)

