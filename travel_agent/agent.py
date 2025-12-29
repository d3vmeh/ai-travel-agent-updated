from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool, google_search
from tools import check_flights, check_hotels, check_weather
from datetime import date

flight_agent = Agent(
    model='gemini-2.0-flash',
    name='flight_agent',
    description='A helpful assistant for flight searches.',
    instruction='You are a helpful assistant that can search for flights.',
    tools=[check_flights],
)

hotel_agent = Agent(
    model='gemini-2.0-flash',
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
    model='gemini-2.0-flash',
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

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    instruction=f"""You are a helpful travel agent that helps people plan out their vacations. You must answer the user's queries in the following steps.
1. Ensure what they are asking is clear. If you are unsure, ask clarifying questions before making the plan.
2. If the user mentions specific requirements or constraints, keep those in mind as you develop the plan
3. Use the tools provided to get important, up-to-date information.

For reference, the current date is: {date.today()}. If the user does not provide the year, assume it is the current year if the date has not already passed.
If the date has passed, then assume it is the next year.

Here are the tools you can use:

- flight_agent: This is a flight planning agent you can ask about the current flights available from one airport to another on a specific date.
- hotel_agent: This is a hotel search agent you can ask about available hotels in a city for specific check-in and check-out dates. It can filter hotels by price range (min/max price per night). The agent returns hotel prices, so you CAN provide pricing information to users.
- weather_agent: This is a weather forecast agent you can ask about the weather forecast on a particular date (up to 16 days in the future). It provides temperature highs/lows, precipitation, and weather conditions.

IMPORTANT: When users specify a budget for hotels, pass those values to the hotel_agent as min_price_per_night and max_price_per_night parameters. The hotel_agent WILL return prices - always show them to the user.

Provide detailed, thorough responses.""",
    tools = [AgentTool(flight_agent), AgentTool(hotel_agent), AgentTool(weather_agent)],
)
