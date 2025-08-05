# In app/services/gemini_service.py

from typing import List
import google.genai as genai
import google.genai.types as types
from app.schemas import GeminiServiceResponse, HistoryMessage, AIResponse
import json

MODEL = 'gemini-2.5-flash-lite'

def load_system_prompt():
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found.")
        return "You are a helpful plant assistant."

SYSTEM_PROMPT = load_system_prompt()

async def get_text_chat_response(
    history: List[HistoryMessage],
    api_key: str,
) -> GeminiServiceResponse:
    """
    Gets a text-only response from Gemini.
    """
    try:
        client = genai.Client(api_key=api_key)
        
        # Build the history for the API. This is now much simpler.
        api_history = []
        for msg in history:
            # Each message is now just text.
            parts = [types.Part(text=msg.content)]
            api_history.append(types.Content(role=msg.role, parts=parts))

        # --- Call the API ---
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=800,
                response_mime_type="application/json",
                response_schema=AIResponse.model_json_schema(),
            )
        )
        
        # Parse the structured JSON response
        try:
            ai_output = AIResponse.model_validate_json(response.text)
            response_text = ai_output.response
            follow_ups = ai_output.follow_up_questions
        except Exception:
            response_text = response.text
            follow_ups = []

        usage = response.usage_metadata
        return GeminiServiceResponse(
            response_text=response_text,
            follow_ups=follow_ups,
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count
        )
    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        raise e