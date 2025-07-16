import os
from dotenv import load_dotenv
from typing import List
import google.genai as genai
from google.genai import types
from app import models
from app.schemas import GeminiServiceResponse

# Load environment variables from .env file
load_dotenv()

# Configure the GenAI client
# The new SDK automatically picks up the GEMINI_API_KEY from the environment
try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Google GenAI Client: {e}")
    print("Please ensure your GEMINI_API_KEY is set correctly in the .env file.")
    client = None

MODEL = 'gemini-2.5-flash-lite-preview-06-17'
# It's good practice to load the system prompt from a file
def load_system_prompt():
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found. Using a default prompt.")
        return "You are a helpful assistant."

SYSTEM_PROMPT = load_system_prompt()

async def get_chat_response(history: List[models.ChatMessage]) -> GeminiServiceResponse:
    """
    Gets a response from the Gemini API, returning text and token usage.
    """
    if not client:
        # If the client fails, return a default error response
        return GeminiServiceResponse(
            response_text="Error: Gemini client is not configured.",
            input_tokens=0,
            output_tokens=0
        )

    # ... (api_history formatting is the same) ...
    api_history = []
    for msg in history:
        api_role = 'model' if msg.role == 'assistant' else 'user'
        api_history.append({
            "role": api_role,
            "parts": [{"text": msg.content}]
        })

    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=600
            )
        )
        # --- THIS IS THE NEW LOGIC ---
        # Extract token usage from the response metadata
        usage = response.usage_metadata
        return GeminiServiceResponse(
            response_text=response.text,
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count
        )
        # ----------------------------

    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        # Return an error response that still fits our data model
        return GeminiServiceResponse(
            response_text="Oh no! I seem to have a bit of a brain-freeze. 🥶 Please try again in a moment.",
            input_tokens=0,
            output_tokens=0
        )