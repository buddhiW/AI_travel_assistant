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

        # return {"messages": [
        #     HumanMessage(content=result["messages"][-1].content)
        # ]
        # }
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
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
        }

    return entry_node


## TO DO: Arrange this script
members = ["entry_duration", "entry_traffic", "entry_transit"]
options = members + ["FINISH"]

class Router(TypedDict):
    """Worker to route to next. No need for an explicit FINISH output because conditional edges can to END."""
    next: Literal[*members]

## Supervising agent that calls the tools as it sees fit.
supervisor_agent = Agent(
    name = "triage agent",
    instructions = "You are a helpful agent that is tasked with managing a conversation between the"
                    f" following workers: {members}. "
                    "Gather information to direct the user to the correct worker out of travel duration, "
                    "traffic conditions, transit route and transit schedule. "
                    "For any other travel questions, make up an informative answer. Answer in at most two sentences. "
                    "Allow questions that are tangential, as long as they fulfill the goal of providing information related to travel."
                    "If the query is not relevant, politely ask the user to ask relevant questions. ",
)
    
travel_duration_agent = Agent(
    name = "travel duration agent",
    instructions= "Your are an agent that computes travel duration using origin, destination and travel mode. "
                    "If the question is not relevant, pass back to supervisor. ",
    tools= [compute_travel_duration,],
)

traffic_updates_agent = Agent(
    name = "traffic condition agent",
    instructions = "You are an agent that provides real-time traffic updates for a route. "
                    "If the question is not relevant, pass back to supervisor. ",
    tools = [traffic_condition,],
)

# transit_route_agent = Agent(
#     name = "transit route agent",
#     instructions = "You are an agent that provides the transit route (bus, train, tram) given origin, destination. "
#                     "If the mode of travel is not transit, that is bus, train, tram, ask the user to input a valid mode of travel. "
#                     "If the question is not relevant, pass back to supervisor. ",
#     tools = [find_route,],
# )

transit_details_agent = Agent(
    name = "transit details agent",
    instructions = "You are an agent that provides information related to transit (bus, train, tram) routes and schedules, given origin, destination. "
                    "If the mode of travel is not transit, that is bus, train, tram, ask the user to input a valid mode of travel. "
                    "If the question is not relevant, pass back to supervisor. ",
    tools = [find_route, find_transit_schedule,],
)

