# AI Travel Agent

An AI-powered travel assistant that uses Google's Agent Development Kit, capable of searching flights, hotels, and providing travel information through web search.

## Features

- **Flight Search**: Search for available flights using the Amadeus API
  - Get real-time flight availability and pricing
  - Support for multiple airlines
  - View departure/arrival times and seat availability

- **Hotel Search**: Search for available hotels using the Amadeus API
  - Find hotels in cities worldwide
  - Filter by price range (min/max per night)
  - Get pricing, ratings, and room details
  - View hotel addresses and amenities

- **Weather Forecast**: Check weather forecasts using Open-Meteo API
  - Get forecasts up to 16 days in advance
  - View temperature highs/lows, precipitation, and conditions
  - Free with no API key required

- **Web Search**: Search the web for travel-related information
  - Find destination guides, travel tips, and recommendations
  - Search for attractions, restaurants, and activities

## Setup

### Prerequisites

- Python 3.12 or higher
- A Google API key (for Gemini)
- Amadeus API credentials (for flight and hotel search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/d3vmeh/ai-travel-agent-updated.git
   cd ai-travel-agent-updated
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root directory with the following:
   ```
   GOOGLE_API_KEY=your-google-api-key
   AMADEUS_CLIENT_ID=your-amadeus-client-id
   AMADEUS_CLIENT_SECRET=your-amadeus-client-secret
   ```

   - Get a Google API key from [Google AI Studio](https://aistudio.google.com/)
   - Get Amadeus credentials from [Amadeus for Developers](https://developers.amadeus.com/)

## Running the Agent

Navigate to the project root directory (where `.env` and `travel_agent/` are located) and run:

```bash
adk web --port 8000
```

This will start the web UI server. Open your browser and navigate to:

```
http://localhost:8000
```

You can now interact with the travel agent through the web interface to:
- Search for flights between airports (use IATA codes like SFO, LAX, JFK)
- Find hotels in cities with optional price filtering
- Check weather forecasts for specific dates (up to 16 days ahead)
- Get travel recommendations and destination information via web search
