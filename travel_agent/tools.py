from typing import List, Dict, Optional
import requests
import os
from datetime import datetime
from amadeus import Client, ResponseError
from ddgs import DDGS
from bs4 import BeautifulSoup
import random
import time
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)


def check_flights(destination: str, departure_date: str, origin: str) -> dict:
    """
    Check available flights for a given destination and date.

    Args:
        destination (str): IATA code of destination airport (e.g., 'JFK' for New York JFK)
        departure_date (str): Date in format mm/dd/yy (e.g., '12/13/25' for December 13, 2025)
        origin (str): IATA code of origin airport (e.g., 'LAX' for Los Angeles)

    Returns:
        dict: Dictionary with 'status' and 'flights' or 'error' containing flight details
    """
    airline_names = {
        'BA': 'British Airways',
        'AF': 'Air France',
        'LH': 'Lufthansa',
        'AA': 'American Airlines',
        'UA': 'United Airlines',
        'DL': 'Delta Air Lines',
        'EK': 'Emirates',
        'IB': 'Iberia',
        'KL': 'KLM Royal Dutch Airlines',
        'QF': 'Qantas',
        'F9': 'Frontier Airlines',
        'W2': 'FlexFlight',
        'WN': 'Southwest Airlines',
        'B6': 'JetBlue Airways',
        'AS': 'Alaska Airlines',
        'NK': 'Spirit Airlines',
        'WS': 'WestJet',
        'AC': 'Air Canada',
        'VS': 'Virgin Atlantic',
        'TK': 'Turkish Airlines',
        'LX': 'Swiss International Air Lines',
        'OS': 'Austrian Airlines',
        'AY': 'Finnair',
        'SK': 'SAS Scandinavian Airlines',
        'EI': 'Aer Lingus',
        'TP': 'TAP Air Portugal',
        'LO': 'LOT Polish Airlines',
        'AZ': 'ITA Airways',
        'SN': 'Brussels Airlines'
    }

    try:
        formatted_date = datetime.strptime(departure_date, '%m/%d/%y').strftime('%Y-%m-%d')
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=formatted_date,
            adults=1,
            max=5, 
            currencyCode='USD'
        )
        
        if response.data:
            flights = []
            for offer in response.data:
                airline_code = offer['validatingAirlineCodes'][0]
                airline_name = airline_names.get(airline_code, airline_code)

                departure_time = datetime.fromisoformat(offer['itineraries'][0]['segments'][0]['departure']['at'].replace('Z', '+00:00'))
                arrival_time = datetime.fromisoformat(offer['itineraries'][0]['segments'][-1]['arrival']['at'].replace('Z', '+00:00'))

                flight = {
                    'airline': airline_name,
                    'departure': departure_time.strftime('%m/%d/%y %I:%M %p'),
                    'arrival': arrival_time.strftime('%m/%d/%y %I:%M %p'),
                    'price': f"${float(offer['price']['total']):.2f}",
                    'seats_remaining': offer['numberOfBookableSeats']
                }
                flights.append(flight)
            return {"status": "success", "flights": flights}

        return {"status": "error", "error": "No flights found"}
    
    except ResponseError as e:
        return {"status": "error", "error": f"Error checking flights: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


def web_search(query: str, num_results: int) -> dict:
    """
    Perform a web search and return search results.

    Args:
        query (str): Search query
        num_results (int): Number of results to return

    Returns:
        dict: Dictionary with 'status' and 'results' or 'error' containing search results
    """
    try:
        ddgs = DDGS()
        search_results = list(ddgs.text(query, max_results=num_results))

        if not search_results:
            return {"status": "error", "error": "No search results found"}

        results = []
        for result in search_results:
            formatted_result = {
                'title': result.get('title', 'No title'),
                'summary': result.get('body', 'No summary'),
                'url': result.get('href', '')
            }
            results.append(formatted_result)

        return {"status": "success", "results": results}

    except Exception as e:
        return {"status": "error", "error": f"Error performing web search: {str(e)}"}