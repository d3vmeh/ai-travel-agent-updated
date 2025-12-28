from google.adk.agents.llm_agent import Agent
from google.adk.tools import AgentTool
from tools import check_flights, web_search


flight_agent = Agent(
    model='gemini-2.0-flash',
    name='flight_agent',
    description='A helpful assistant for flight searches.',
    instruction='You are a helpful assistant that can search for flights.',
    tools=[check_flights],
)

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    instruction='You are a helpful travel agent that helps people plan out their vacations. You can talk to flight_agent who can tell you what flights are available.',
    tools = [AgentTool(flight_agent)],
)
