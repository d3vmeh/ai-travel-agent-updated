from typing import List, Dict, Optional
import requests
import os
from datetime import datetime
from amadeus import Client, ResponseError
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import random
import time
from dotenv import load_dotenv

load_dotenv()

amadeus = Client(
    client_id=os.getenv('AMADEUS_CLIENT_ID'),
    client_secret=os.getenv('AMADEUS_CLIENT_SECRET')
)



def check_flights(destination: str, departure_date: str, origin: str = "LON") -> Optional[List[Dict]]:
    """
    Check available flights for a given destination and date.
    
    Args:
        destination (str): IATA code of destination airport (e.g., 'NYC' for New York)
        departure_date (str): Date in format mm/dd/yy
        origin (str): IATA code of origin airport (default: 'LON' for London)

    Returns:
        Optional[List[Dict]]: List of available flights with their details, or None if no flights are found
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
            return flights
        
        return None
    
    except ResponseError as e:
        print(f"Error checking flights: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def get_todays_date() -> str:
    """
    Get today's date in mm/dd/yy format.
    
    Returns:
        str: Today's date formatted as mm/dd/yy
    """
    return datetime.now().strftime('%m/%d/%y')

def web_search(query: str, num_results: int = 5) -> Optional[List[str]]:
    """
    Perform a web search and return content from the top results in a text-only format.
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return (default: 5)

    Returns:
        Optional[List[str]]: List of formatted text results, or None if the search fails
    """
    try:
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]

        ddgs = DDGS()
        search_results = list(ddgs.text(query, max_results=num_results))
        
        results = []
        for result in search_results:
            time.sleep(random.uniform(1, 3))
            
            try:
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                }
                
                response = requests.get(
                    result['href'],
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for script in soup(['script', 'style', 'meta', 'link']):
                    script.decompose()
                
                text = ' '.join(soup.stripped_strings)
                text = text[:2000] + '...' if len(text) > 2000 else text
                
                formatted_result = f"""
                Source: {result['title']}
                Summary: {result['body']}
                Content: {text}
                ----------------------------------------
                """
                results.append(formatted_result)
                
            except Exception as e:
                print(f"Error scraping content: {str(e)}")
                continue
        
        return results if results else None
    
    except Exception as e:
        print(f"Error performing web search: {str(e)}")
        return None