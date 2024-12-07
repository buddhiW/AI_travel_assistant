import os
import requests
from dotenv import load_dotenv

def compute_travel_duration(origin, destination, mode_of_travel, use_api=False):
    """
    Function to compute travel duration given origin, destination and mode of travel.
    The output of this function is a string, that is used by the LLM to produce the response.
    """
    load_dotenv()
    map_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if use_api == True:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "mode": mode_of_travel,
            "key": map_api_key
        }

        errors = ''

        # Google Maps API call
        response = requests.get(url, params=params).json()
        
        origin_address = response['origin_addresses'][0]
        destination_address = response['destination_addresses'][0]

        if response['status'] == 'OK' and response['rows'][0]['elements'][0]['status'] == 'OK':
            duration = response['rows'][0]['elements'][0]['duration']['text']
            output = f'Time to travel from  {origin_address} to {destination_address} by {mode_of_travel} is {duration}.'
            return output
        elif not destination_address:
            errors + 'not enough information to determine destination address '
        elif not origin_address:
            errors + ' not enough information to determine origin address'

        return errors
    else:
        ## Time is hard-coded. In reality, this would be an API call.
        output = f'Time to travel from  {origin} to {destination} by {mode_of_travel} is 1 hour.'
        return output

def traffic_condition(route):
    """
    This function takes a route as input and returns traffic conditions for ground travel.
    A route could be a number or an origin and destination.
    """
    return f'There is heavey traffic between cityA and cityB on {route}, which could add 20 minutes to the journey'

def find_route(origin, destination, mode_of_travel):
    """
    This function takes origin, destination, mode of travel and returns the transit route number. 
    """
    ## Route number is hard-coded
    route_number = "425"
    print(f'Found {mode_of_travel} route from {origin} to {destination}: {route_number}')
    return route_number

def find_transit_schedule(route_number, mode_of_travel):
    """
    This function returns the schedule for the route number.
    """
    print("Looking up transit schedules.")
    output = f'The next {route_number} {mode_of_travel} leaves at 10.30AM. Next one is scheduled at 11.30 AM.'
    return output