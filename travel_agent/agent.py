from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool, google_search
from datetime import date
from typing import List, Dict, Optional
import requests
import os
from datetime import datetime
from amadeus import Client, ResponseError
from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
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
            max=25, 
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


def check_hotels(city_code: str, check_in_date: str, check_out_date: str, adults: int = 1, min_price_per_night: float = 0, max_price_per_night: float = 10000) -> dict:
    """
    Search for available hotels in a city with optional price filtering.

    Args:
        city_code (str): IATA city code (e.g., 'NYC' for New York, 'PAR' for Paris)
        check_in_date (str): Check-in date in format mm/dd/yy (e.g., '12/13/25')
        check_out_date (str): Check-out date in format mm/dd/yy (e.g., '12/15/25')
        adults (int): Number of adults (default: 1)
        min_price_per_night (float): Minimum price per night in USD (default: 0)
        max_price_per_night (float): Maximum price per night in USD (default: 10000)

    Returns:
        dict: Dictionary with 'status' and 'hotels' or 'error' containing hotel details
    """
    try:
        formatted_check_in = datetime.strptime(check_in_date, '%m/%d/%y').strftime('%Y-%m-%d')
        formatted_check_out = datetime.strptime(check_out_date, '%m/%d/%y').strftime('%Y-%m-%d')

        hotels_list_response = amadeus.reference_data.locations.hotels.by_city.get(
            cityCode=city_code
        )

        if not hotels_list_response.data:
            return {"status": "error", "error": "No hotels found in this city"}

        hotel_ids = [hotel['hotelId'] for hotel in hotels_list_response.data[:100]]

        if not hotel_ids:
            return {"status": "error", "error": "No hotel IDs available"}

        hotels = []

        batch_size = 10
        for i in range(0, min(len(hotel_ids), 100), batch_size):
            batch_ids = hotel_ids[i:i+batch_size]
            hotel_ids_str = ','.join(batch_ids)

            try:
                offers_response = amadeus.shopping.hotel_offers_search.get(
                    hotelIds=hotel_ids_str,
                    checkInDate=formatted_check_in,
                    checkOutDate=formatted_check_out,
                    adults=adults,
                    currency='USD'
                )

                if offers_response.data:
                    for offer_group in offers_response.data:
                        hotel_data = offer_group.get('hotel', {})

                        offers = offer_group.get('offers', [])
                        if not offers:
                            continue

                        first_offer = offers[0]
                        price_data = first_offer.get('price', {})
                        room_data = first_offer.get('room', {})

                        price_per_night = float(price_data.get('base', 0))

                        if price_per_night < min_price_per_night or price_per_night > max_price_per_night:
                            continue

                        hotel = {
                            'name': hotel_data.get('name', 'Unknown Hotel'),
                            'rating': hotel_data.get('rating', 'N/A'),
                            'price_per_night': f"${price_per_night:.2f}",
                            'total_price': f"${float(price_data.get('total', 0)):.2f}",
                            'currency': price_data.get('currency', 'USD'),
                            'room_type': room_data.get('typeEstimated', {}).get('category', 'Standard'),
                            'beds': room_data.get('typeEstimated', {}).get('beds', 'N/A')
                        }
                        hotels.append(hotel)

                        if len(hotels) >= 15:
                            break

            except ResponseError as batch_error:
                continue

            if len(hotels) >= 15:
                break

        if hotels:
            hotels.sort(key=lambda x: float(x['total_price'].replace('$', '')))
            return {"status": "success", "hotels": hotels[:10]}
        else:
            if min_price_per_night > 0 or max_price_per_night < 10000:
                return {"status": "error", "error": f"No hotels found in the ${min_price_per_night:.0f}-${max_price_per_night:.0f} per night price range for the specified dates. Try widening your price range or different dates."}
            else:
                return {"status": "error", "error": "No available hotel offers found for the specified dates"}

    except ResponseError as e:
        return {"status": "error", "error": f"Error checking hotels: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}

def check_weather(location: str, date: str) -> dict:
    """
    Get the weather forecast for a specific location and date.
    Uses Open-Meteo API which provides free weather forecasts up to 16 days.

    Args:
        location (str): The location to get the weather for (city name)
        date (str): Date in format mm/dd/yy (e.g., '01/15/26')

    Returns:
        dict: Dictionary with 'status' and 'weather' or 'error' containing forecast information
    """
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        geo_response = requests.get(geocode_url)
        geo_data = geo_response.json()

        if not geo_data.get('results'):
            return {"status": "error", "error": f"Could not find location: {location}"}

        latitude = geo_data['results'][0]['latitude']
        longitude = geo_data['results'][0]['longitude']
        location_name = geo_data['results'][0]['name']
        country = geo_data['results'][0].get('country', '')

        formatted_date = datetime.strptime(date, '%m/%d/%y').strftime('%Y-%m-%d')

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode,windspeed_10m_max"
            f"&temperature_unit=fahrenheit&windspeed_unit=mph&precipitation_unit=inch"
            f"&timezone=auto"
            f"&start_date={formatted_date}&end_date={formatted_date}"
        )

        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        if weather_response.status_code != 200 or 'daily' not in weather_data:
            return {"status": "error", "error": "Could not retrieve weather data for the specified date"}

        daily = weather_data['daily']

        weather_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
            82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
            95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
        }

        weather_code = daily['weathercode'][0]
        description = weather_codes.get(weather_code, "Unknown")

        weather_info = {
            'location': f"{location_name}, {country}" if country else location_name,
            'date': formatted_date,
            'temperature_high': f"{daily['temperature_2m_max'][0]:.1f}°F",
            'temperature_low': f"{daily['temperature_2m_min'][0]:.1f}°F",
            'description': description,
            'precipitation': f"{daily['precipitation_sum'][0]:.2f} inches",
            'precipitation_probability': f"{daily['precipitation_probability_max'][0]}%",
            'max_wind_speed': f"{daily['windspeed_10m_max'][0]:.1f} mph"
        }

        return {"status": "success", "weather": weather_info}

    except ValueError as e:
        return {"status": "error", "error": f"Invalid date format. Please use mm/dd/yy format: {str(e)}"}
    except requests.RequestException as e:
        return {"status": "error", "error": f"Error contacting weather service: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Error getting weather forecast: {str(e)}"}


def check_car_rentals(
    pickup_location: str,
    pickup_date: str,
    dropoff_date: str,
    pickup_time: str = "10:00",
    dropoff_time: str = "10:00"
) -> dict:
    """
    Search for available car rentals at airports or cities.

    Args:
        pickup_location (str): Airport IATA code (e.g., 'LAX', 'JFK', 'ORD')
        pickup_date (str): Pickup date in format mm/dd/yy (e.g., '12/13/25')
        dropoff_date (str): Drop-off date in format mm/dd/yy (e.g., '12/15/25')
        pickup_time (str): Pickup time in HH:MM format (default: '10:00')
        dropoff_time (str): Drop-off time in HH:MM format (default: '10:00')

    Returns:
        dict: Dictionary with 'status' and 'cars' or 'error' containing rental details
    """
    try:
        formatted_pickup = datetime.strptime(pickup_date, '%m/%d/%y').strftime('%Y-%m-%d')
        formatted_dropoff = datetime.strptime(dropoff_date, '%m/%d/%y').strftime('%Y-%m-%d')

        url = "https://booking-com15.p.rapidapi.com/api/v1/cars/searchCarRentals"

        headers = {
            "x-rapidapi-key": os.getenv('RAPIDAPI_KEY'),
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        params = {
            "pick_up_location": pickup_location,
            "pick_up_date": formatted_pickup,
            "pick_up_time": pickup_time,
            "drop_off_date": formatted_dropoff,
            "drop_off_time": dropoff_time,
            "currency_code": "USD"
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if response.status_code != 200:
            return {"status": "error", "error": f"API request failed: {response.status_code}"}

        if not data.get('data') or not data['data'].get('search_results'):
            return {"status": "error", "error": "No car rentals found for the specified location and dates"}

        cars = []
        for car in data['data']['search_results'][:20]:
            vehicle = car.get('vehicle_info', {})
            pricing = car.get('pricing_info', {})
            supplier = car.get('supplier_info', {})

            car_info = {
                'company': supplier.get('name', 'Unknown'),
                'car_type': vehicle.get('group', 'Standard'),
                'car_name': vehicle.get('v_name', 'N/A'),
                'transmission': vehicle.get('transmission', 'Automatic'),
                'seats': vehicle.get('seats', 'N/A'),
                'bags': vehicle.get('baggage', 'N/A'),
                'air_conditioning': vehicle.get('aircon', False),
                'price_per_day': f"${float(pricing.get('price_per_day', 0)):.2f}",
                'total_price': f"${float(pricing.get('total_price', pricing.get('price', 0))):.2f}",
                'fuel_policy': car.get('fuel_policy', 'N/A'),
                'mileage': car.get('mileage', 'Unlimited')
            }
            cars.append(car_info)

        if cars:
            cars.sort(key=lambda x: float(x['total_price'].replace('$', '')))
            return {"status": "success", "cars": cars[:10]}

        return {"status": "error", "error": "No car rentals found for the specified dates"}

    except ValueError as e:
        return {"status": "error", "error": f"Invalid date format. Use mm/dd/yy: {str(e)}"}
    except requests.RequestException as e:
        return {"status": "error", "error": f"Error contacting car rental service: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Error searching car rentals: {str(e)}"}


flight_agent = Agent(
    model='gemini-2.5-flash',
    name='flight_agent',
    description='A helpful assistant for flight searches.',
    instruction='You are a helpful assistant that can search for flights.',
    tools=[check_flights],
)

hotel_agent = Agent(
    model='gemini-2.5-flash',
    name='hotel_agent',
    description='A helpful assistant for hotel searches with price filtering.',
    instruction="""You are a helpful assistant that can search for available hotels in cities.

When searching for hotels, you can filter by price using the min_price_per_night and max_price_per_night parameters.
The check_hotels function returns hotels with the following information:
- name: Hotel name
- rating: Hotel rating
- price_per_night: Price per night in USD (this is the nightly rate)
- total_price: Total price for the entire stay
- room_type: Type of room
- beds: Number of beds

IMPORTANT: The prices ARE included in the results. Always present the price_per_night and total_price to the user.
When the user specifies a budget (e.g., $150-$250 per night), use the min_price_per_night and max_price_per_night parameters to filter results.""",
    tools=[check_hotels],
)

weather_agent = Agent(
    model='gemini-2.5-flash',
    name='weather_agent',
    description='A helpful assistant for checking weather forecasts on specific dates',
    instruction="""You are a helpful assistant that can check weather forecasts for specific dates up to 16 days in the future.

The check_weather function requires:
- location (str): City name (e.g., 'Los Angeles', 'New York', 'Paris')
- date (str): Date in format mm/dd/yy (e.g., '01/15/26')

The function returns weather information including:
- temperature_high: Maximum temperature for the day
- temperature_low: Minimum temperature for the day
- description: Weather conditions (clear, cloudy, rain, snow, etc.)
- precipitation: Expected precipitation amount
- precipitation_probability: Chance of precipitation
- max_wind_speed: Maximum wind speed

IMPORTANT: Always present the weather information clearly to the user, including both high and low temperatures.""",
    tools=[check_weather]
)

web_search_agent = Agent(
    model='gemini-2.5-flash',
    name='web_search_agent',
    description='An assistant with the ability to search Google',
    instruction='You are a helpful assistant who can conduct web searches',
    tools=[google_search]
)

car_rental_agent = Agent(
    model='gemini-2.5-flash',
    name='car_rental_agent',
    description='A helpful assistant for searching car rentals at airports and cities.',
    instruction="""You are a helpful assistant that searches for car rentals.

The check_car_rentals function requires:
- pickup_location (str): Airport IATA code (e.g., 'LAX', 'JFK', 'ORD', 'CDG')
- pickup_date (str): Pickup date in mm/dd/yy format
- dropoff_date (str): Drop-off date in mm/dd/yy format
- pickup_time (str): Optional, defaults to '10:00'
- dropoff_time (str): Optional, defaults to '10:00'

The function returns car rental information including:
- company: Rental company name (Hertz, Enterprise, Avis, etc.)
- car_type: Vehicle class (Economy, Compact, SUV, etc.)
- car_name: Specific vehicle model
- transmission: Automatic or Manual
- seats: Passenger capacity
- bags: Luggage capacity
- air_conditioning: Whether AC is included
- price_per_day: Daily rental rate in USD
- total_price: Total cost for the rental period
- fuel_policy: Fuel policy details
- mileage: Mileage allowance (often Unlimited)

IMPORTANT: Always present pricing clearly (both per-day and total) and help users compare options by vehicle type and rental company.""",
    tools=[check_car_rentals]
)

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    instruction=f"""You are a helpful travel agent that helps people plan out their vacations. You must answer the user's queries in the following steps.
1. Ensure what they are asking is clear. If you are unsure, ask clarifying questions before making the plan.
2. If the user mentions specific requirements or constraints, keep those in mind as you develop the plan
3. Use the tools provided to get important, up-to-date information.

For reference, the current date is: {date.today()}. If the user does not provide the year, assume it is the current year if the date has not already passed.
If the date has passed, then assume it is the next year.

Here are the tools you can use to develop the full plan:

- flight_agent: This is a flight planning agent you can ask about the current flights available from one airport to another on a specific date.
- hotel_agent: This is a hotel search agent you can ask about available hotels in a city for specific check-in and check-out dates. It can filter hotels by price range (min/max price per night). The agent returns hotel prices, so you CAN provide pricing information to users.
- weather_agent: This is a weather forecast agent you can ask about the weather forecast on a particular date (up to 16 days in the future). It provides temperature highs/lows, precipitation, and weather conditions.
- car_rental_agent: This is a car rental search agent you can ask about available rental cars at airports or cities. It returns pricing, vehicle types (economy, compact, SUV, etc.), rental companies, and details like transmission type and passenger capacity.
- web_search_agent: This is a web search agent that you can use to search up queries on Google. It can provide useful information on recent news and suggested activities for the user to visit.

IMPORTANT: When users specify a budget for hotels, pass those values to the hotel_agent as min_price_per_night and max_price_per_night parameters. The hotel_agent WILL return prices - always show them to the user.

Provide detailed, thorough responses.""",
    tools = [AgentTool(flight_agent), AgentTool(hotel_agent), AgentTool(weather_agent), AgentTool(car_rental_agent), AgentTool(web_search_agent)],
)
