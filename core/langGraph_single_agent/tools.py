from langchain_core.tools import tool

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
    ## Route number is hard-coded.
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