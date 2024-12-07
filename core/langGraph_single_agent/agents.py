from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from pydantic import BaseModel

from tools import *

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

## This general agent class can be used to define various agents, including an assistant agent.
## Note that langgraph has a prebuilt agent that can be created through create_react_agent(). 
## However, creating our own agents offers better flexibility.
class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "Your are a helpful Agent"
    tools: list = []

## Executing the runnable assistant agent
class Assistant:

    def __init__(self, runnable: Runnable):
        self.runnable = runnable
    
    def __call__(self, state: State, config: RunnableConfig):

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

## Supervising agent that calls the tools as it sees fit.
triage_agent = Agent(
    name = "triage agent",
    instructions = "You are a helpful agent that helps users plan trips and travels by providing useful information. "
                    "Introduce yourself very briefly. "
                    "Gather information to direct the user to the correct department out of travel duration, "
                    "traffic conditions, find transit route and find transit schedule. "
                    "For any other travel questions, make up an informative answer. Answer in at most two sentences. "
                    "Allow questions that are tangential, as long as they fulfill the goal of providing information related to travel."
                    "If the query is not relevant, politely ask the user to ask relevant questions. ",
    tools = [
        compute_travel_duration,
        traffic_condition,
        find_route,
        find_transit_schedule,
    ]
)
    


