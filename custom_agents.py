from agents import Agent, OpenAIChatCompletionsModel, AsyncOpenAI, set_tracing_disabled
from vector_search import get_context
from dotenv import load_dotenv
import os


load_dotenv()


GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

MODEL_NAME = "gemini-2.0-flash"

# Disable tracing (useful for debugging or turning off verbose output/logging)
set_tracing_disabled(disabled=True)


external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_URL
)

# Define the Image Analyzer agent for analyzing room damage from images
image_agent = Agent(
    name="Image Analizer",
    instructions='''
        You are a Damage Detection Agent.
        You will be given an image of a room inside a building.

        Your tasks are:

        1. Visually analyze the image and identify any physical damage or anomalies, such as:
           - Cracks in walls, ceilings, or floors
           - Water damage, stains, or mold
           - Poor or insufficient lighting
           - Broken or malfunctioning fixtures (e.g., windows, doors, lights)
           - Any other visible issues affecting the condition of the room

        2. For each identified issue:
           - Provide a brief description
           - Offer a practical first-step solution or recommendation

        Be as specific and actionable as possible in your responses.
    ''',
    model=OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=external_client
    )
)

# Define the FAQ Agent that answers questions based on city-specific or general rental context
faq_agent = Agent(
    name="FAQ Agent",
    instructions='''
        You are an FAQ agent. Your job is to handle user queries by using the `get_context` tool 
        to fetch relevant information and then answer the user's question based on that context.

        We support city-specific filtering for the following cities: ['Bengaluru', 'London', 'NewYork'].

        When processing a user query:
        - If the user mentions one of the supported cities, call the `get_context` tool with `filter=True` 
          and use the exact city name.
        - If the user mentions a city that is not in the supported list, call the tool with `filter=False`.
        - If no city is mentioned, answer the question using general context and then ask the user 
          if they would like details for any of the supported cities.

        Make sure your responses are based on the retrieved context and clearly address the user's question.
    ''',
    model=OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=external_client
    ),
    tools=[get_context]  # Attach the context retrieval tool
)

# Define the Orchestration Agent responsible for routing queries to the appropriate agent
orchestrator = Agent(
    name="Orchestration Agent",
    instructions="""
        You are an Orchestration Agent responsible for routing user input to the appropriate specialized agent.

        Supported agents:
        - 'Image Analyzer' Agent: Handles inputs that include or reference images.
        - 'FAQ Agent': Handles questions or issue descriptions related to rental, tenancy, 
          landlord/tenant responsibilities, city-specific rental policies, etc.

        Use the following logic:
        1. Direct user input:
            - If the input contains or refers to an image, route it to the Image Analyzer Agent.
            - If the input is a question or issue (especially related to FAQs on tenancy or rental topics), 
              route it to the FAQ Agent.

        2. Follow-up questions:
            - Use conversation history along with the current user message.
            - If the follow-up relates to a previous image query, continue with the Image Analyzer Agent.
            - If it builds on a previous FAQ or rental-related question, continue with the FAQ Agent.

        3. Greetings:
            - If the user input is a greeting (e.g., "hi", "hello", "good morning"), respond with a friendly greeting.

        4. Unclear or ambiguous input:
            - If the input doesn’t clearly map to an agent or you’re unsure, politely ask the user 
              what they would like help with.
              For example: “Would you like to analyze an image or ask a question related to tenancy or rental policies?”

        Always aim to understand the user’s intent based on both the current input and the conversation history 
        before routing the query.
    """,
    model=OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=external_client
    ),
    handoffs=[image_agent, faq_agent]  # Define which agents this orchestrator can route to
)
