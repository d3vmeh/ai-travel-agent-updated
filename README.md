# AI Travel Agent

An AI-powered travel assistant that uses Google's Agent Development Kit, capable of searching flights and providing travel information through web search.

## Features

- **Flight Search**: Search for available flights using the Amadeus API
  - Get real-time flight availability and pricing
  - Support for multiple airlines
  - View departure/arrival times and seat availability

- **Web Search**: Search the web for travel-related information
  - Find destination guides, travel tips, and recommendations
  - Search for hotels, restaurants, and attractions

## Setup

### Prerequisites

- Python 3.12 or higher
- A Google API key (for Gemini)
- Amadeus API credentials (for flight search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/d3vmeh/ai-travel-agent-updated.git
   cd ai-travel-agent-updated
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate
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
adk run travel_agent
```

This will start a session where you can ask the travel agent to:
- Search for flights between airports
- Get travel recommendations and information via web search