# In app/services/gemini_service.py

from typing import List
import google.genai as genai
from google.genai import types
from app.schemas import GeminiServiceResponse, HistoryMessage
import base64
import magic

MODEL = 'gemini-2.5-flash-lite-preview-06-17'

def load_system_prompt():
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found.")
        return "You are a helpful plant assistant."

SYSTEM_PROMPT = load_system_prompt()

def _create_part_from_base64(b64_string: str) -> types.Part:
    """Decodes a base64 string and creates a Gemini Part object."""
    image_bytes = base64.b64decode(b64_string)
    mime_type = magic.from_buffer(image_bytes, mime=True)
    return types.Part(inline_data=image_bytes, mime_type=mime_type)

# This is now our only service function.
async def get_stateless_chat_response(
    history: List[HistoryMessage], 
    new_message: str,
    api_key: str,
    new_image_b64: str | None
) -> GeminiServiceResponse:
    """
    Gets a response from Gemini using a user-provided API key and history.
    This function is completely stateless.
    """
    try:
        client = genai.Client(api_key=api_key)
        
        api_history = []
        for msg in history:
            parts = [types.Part(text=msg.content)]
            if msg.image_base64:
                try:
                    parts.append(_create_part_from_base64(msg.image_base64))
                except Exception as e:
                    print(f"Could not process a historical image: {e}")
                    parts.append(types.Part(text="[Image could not be loaded]"))
            api_history.append(types.Content(role=msg.role, parts=parts))
        
        final_prompt_parts = [types.Part(text=new_message)]
        if new_image_b64:
            try:
                final_prompt_parts.append(_create_part_from_base64(new_image_b64))
            except Exception as e:
                raise ValueError(f"Invalid Base64 image data provided: {e}")

        api_history.append(types.Content(role='user', parts=final_prompt_parts))
        
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
        raise e