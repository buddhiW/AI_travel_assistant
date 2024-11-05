"""
Author: Buddhi W
Date: 11/5/2024
Agent and function definitions for an AI assistant that answers questions related to travel information including travel duration and traffic conditions.
This implementation is based on https://cookbook.openai.com/examples/orchestrating_agents?utm_source=www.therundown.ai&utm_medium=newsletter&utm_campaign=anthropic-ceo-predicts-ai-utopia&_bhlid=db30852b7747db2f62cd8fde276efcf151c6c21a
"""

from openai import OpenAI
import openai
import requests
from dotenv import load_dotenv
import os
from pydantic import BaseModel

class Agent(BaseModel): 
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "Your are a helpful Agent"
    tools: list = []

def compute_travel_duration(origin, destination, mode_of_travel):
    """
    Function to compute travel duration given origin, destination and mode of travel.
    The output of this function is a string, that is used by the LLM to produce the response.
    """
    ## Time is hard-coded. In reality, this would be an API call.
    output = f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.'
    return output

def traffic_condition(route):
    """
    This function takes route a input and returns real-time traffic updates.
    """
    return f'There is heavey traffic between cityA and cityB on {route}, which could add 20 minutes to the journey'

def find_route(origin, destination, mode_of_travel):
    """
    This function takes origin, destination, mode of travel and returns the transite route number. 
    """
    route_number = "425"
    print(f'Found {mode_of_travel} route from {origin} to {destination}: {route_number}')
    return route_number

def find_transit_schedule(route_number, mode_of_travel):
    """
    This function returns the schedule for the route number.
    """
    print("Looking up transit schedules.")
    output = f'{route_number} {mode_of_travel} leaves at 10.30AM. Next one is scheduled at 11.30 AM.'
    return output

# triage_Agent = Agent(

# )

travel_duration_agent = Agent(
    name = "travel duration agent",
    instructions= "Your are a agent that computes travel duration using origin, destination and travel mode.",
    tools= [compute_travel_duration],
)

traffic_condition_agent = Agent(
    name = "traffic condition agent",
    instructions = "You are an agent that provides real-time traffic updates for a route.",
    tools = [traffic_condition],
)

transit_schedule_agent = Agent(
    name = "transit schedule agent",
    instructions = "You are an agent that provides schedule of a transite route.",
    tools = [find_route, find_transit_schedule],
)