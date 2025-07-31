# In app/services/gemini_service.py

from typing import List
import google.genai as genai
from google.genai import types
from app.schemas import GeminiServiceResponse, HistoryMessage # Import our new schema

MODEL = 'gemini-2.5-flash-lite-preview-06-17'

def load_system_prompt():
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found.")
        return "You are a helpful plant assistant."

SYSTEM_PROMPT = load_system_prompt()

# This is now our only service function.
async def get_stateless_chat_response(
    history: List[HistoryMessage], 
    new_message: str,
    api_key: str
) -> GeminiServiceResponse:
    """
    Gets a response from Gemini using a user-provided API key and history.
    This function is completely stateless.
    """
    try:
        # Create a client for this specific request
        client = genai.Client(api_key=api_key)
        
        # --- Build the prompt contents directly from the input ---
        
        # Convert Pydantic HistoryMessage objects to SDK Content objects
        api_history = [
            types.Content(role=msg.role, parts=[types.Part(text=msg.content)])
            for msg in history
        ]
        
        # Add the new user message to the end of the conversation
        api_history.append(
            types.Content(role='user', parts=[types.Part(text=new_message)])
        )
        
        # --- Call the API ---
        
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=600
            )
        )
        usage = response.usage_metadata
        return GeminiServiceResponse(
            response_text=response.text,
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count
        )

    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        # Re-raise the exception to be handled by the router
        raise e