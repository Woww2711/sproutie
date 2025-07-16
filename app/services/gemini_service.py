import os
from dotenv import load_dotenv
from typing import List
import google.genai as genai
from google.genai import types
from app import models

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

async def get_chat_response(history: List[models.ChatMessage]) -> str:
    """
    Gets a response from the Gemini API, translating roles correctly.
    The 'history' parameter should contain the full conversation, including the latest user message.
    """
    if not client:
        return "Error: Gemini client is not configured."

    # Format the history for the API, translating our internal role "assistant"
    # to the API's required role "model".
    api_history = []
    for msg in history:
        api_role = 'model' if msg.role == 'assistant' else 'user'
        api_history.append({
            "role": api_role,
            "parts": [{"text": msg.content}]
        })
    
    # Now api_history is a correctly formatted list of conversation turns.

    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history, # Pass the translated history
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=700,
            )
        )
        return response.text
    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        return "Oh no! I seem to have a bit of a brain-freeze. 🥶 Please try again in a moment."