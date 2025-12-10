from google.adk.agents.llm_agent import Agent
from tools import check_flights, web_search

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description='A helpful assistant for flight searches and web searches.',
    instruction='You are a helpful assistant that can search for flights and search the web for information.',
    tools=[check_flights, web_search],
)