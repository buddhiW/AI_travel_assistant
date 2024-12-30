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

from langchain_core.tools import tool
from pydantic import BaseModel, Field

@tool
def compute_travel_duration(origin, destination, mode_of_travel):
    """
    Function to compute travel duration given origin, destination and mode of travel.
    The output of this function is a string, that is used by the LLM to produce the response.
    """
    ## Time is hard-coded. In reality, this would be an API call.
    output = f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.'
    return output

@tool
def traffic_condition(route):
    """
    This function takes route as input and returns real-time traffic updates.
    """
    return f'There is heavey traffic between cityA and cityB on {route}, which could add 20 minutes to the journey'

@tool
def find_route(origin, destination, mode_of_travel):
    """
    This function takes origin, destination, mode of travel and returns the transit route number. 
    """
    route_number = "425"
    print(f'Found {mode_of_travel} route from {origin} to {destination}: {route_number}')
    return route_number

@tool
def find_transit_schedule(route_number, mode_of_travel):
    """
    This function returns the schedule for the route number.
    """
    print("Looking up transit schedules.")
    output = f'The next {route_number} {mode_of_travel} leaves at 10.30AM. Next one is scheduled at 11.30 AM.'
    return output

## Transfer tools
class transfer_to_travel_duration_agent(BaseModel):
    """
    Transfer to a specialized assistant for computing travel duration
    """
    origin: str = Field(description="The origin location of the trip.")
    destination: str = Field(description="The destination location of the trip.") 
    mode_of_travel: str = Field(description="The model of travel.")

class transfer_to_traffic_updates_agent(BaseModel):
    """
    Transfer to a specialized assistant for providing traffic condition updates for given routes
    """
    route: str = Field(description="Route to compute traffic conditions")

class transfer_to_transit_details_agent(BaseModel):
    """
    Transfer to a specialized assistant for details related to transit travel
    """
    route_number: str = Field(description="Transit route number")
    mode_of_travel: str = Field(description="Mode of transit")

class transfer_back_to_triage_agent(BaseModel):
    """
    Transfer the control back to triage agent
    """

