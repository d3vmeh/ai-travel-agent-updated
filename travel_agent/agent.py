from google.adk.agents.llm_agent import Agent
from tools import check_flights, web_search
from google.adk.tools import google_search

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge. Use the google_search tool provided to get the information you need.',
    tools=[google_search],
)
