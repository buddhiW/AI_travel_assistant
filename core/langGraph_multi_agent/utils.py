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

"""
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from langgraph.prebuilt import ToolNode

from agents import *
from tools import *

def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

def route_tools(state:State):
    route = tools_condition(state)

    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls

    if tool_calls:

        leave = any(tc["name"] == transfer_back_to_triage_agent.__name__ for tc in tool_calls)
        if leave:
            return "leave_skill"
        if all(tc["name"] in [t.name for t in travel_duration_agent.tools] for tc in tool_calls):
            return "travel_duration_tools"
        if all(tc["name"] in [t.name for t in traffic_updates_agent.tools] for tc in tool_calls):
            return "traffic_updates_tools"
        if all(tc["name"] in [t.name for t in transit_details_agent.tools] for tc in tool_calls):
            return "transit_details_tools"
    
    raise ValueError("Invalid route")

def route_triage_assistant(
    state: State,
):
    ## tools_condition adds an edge between assistant and END
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == transfer_to_travel_duration_agent.__name__:
            return "enter_travel_duration"
        elif tool_calls[0]["name"] == transfer_to_traffic_updates_agent.__name__:
            return "enter_traffic_updates"
        elif tool_calls[0]["name"] == transfer_to_transit_details_agent.__name__:
            return "enter_transit_details"
        
    raise ValueError("Invalid route")

def return_control(state:State):
    """
    Return the control back to the triage agent to resume the conversation.
    """

    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the triage assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "messages": messages,
    }
