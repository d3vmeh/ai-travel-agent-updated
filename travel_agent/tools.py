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
            max=15, 
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
