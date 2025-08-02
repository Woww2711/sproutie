# In app/services/gemini_service.py

from typing import List
from fastapi import UploadFile
import google.genai as genai
import google.genai.types as types
from app.schemas import GeminiServiceResponse, HistoryMessage
import asyncio

MODEL = 'gemini-2.5-flash-lite'

def load_system_prompt():
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found.")
        return "You are a helpful plant assistant."

SYSTEM_PROMPT = load_system_prompt()

# --- This function handles the initial upload ---
async def upload_file_to_gemini(file: UploadFile, api_key: str) -> types.File:
    """Uploads a file using a temporary client initialized with the user's API key."""
    try:
        client = genai.Client(api_key=api_key)
        print(f"Uploading file '{file.filename}' to Gemini Files API...")
        uploaded_file = await client.aio.files.upload(
            file=file.file,
            config=types.UploadFileConfig(mime_type=file.content_type)
        )
        print(f"Successfully uploaded file. API Name: {uploaded_file.name}")
        return uploaded_file
    except Exception as e:
        print(f"An error occurred during file upload to Gemini: {e}")
        raise e

# --- This is the main chat function, implementing our test script's logic ---
async def get_multimodal_chat_response(
    history: List[HistoryMessage],
    api_key: str,
) -> GeminiServiceResponse:
    """
    Gets a multimodal response from Gemini, retrieving files from references.
    The last message in the history is considered the current user prompt.
    """
    try:
        client = genai.Client(api_key=api_key)
        
        # Build the full history for the API
        api_history = []
        for msg in history:
            # For each message, retrieve the files it references
            file_references = msg.file_references or []
            print(f"Processing message: {msg.role} - {msg.content[:30]}... | file_references: {file_references}")
            file_objects = []
            if file_references:
                for ref in file_references:
                    print(f"  Attempting to retrieve file reference: {ref}")
                try:
                    get_file_tasks = [client.aio.files.get(name=name) for name in file_references]
                    # Add a timeout to file retrieval (e.g., 10 seconds)
                    file_objects = await asyncio.wait_for(asyncio.gather(*get_file_tasks), timeout=10)
                    print(f"Retrieved file objects: {[f.name for f in file_objects]}")
                except asyncio.TimeoutError:
                    print(f"Timeout retrieving files: {file_references}")
                    # Optionally, you could raise or skip
                except Exception as e:
                    # Handle cases where a file might have expired (48h)
                    print(f"Error retrieving a historical file: {e}")
                    import traceback
                    traceback.print_exc()
                    # We'll just skip this file and proceed
            # Create the 'parts' for this turn, including text and any retrieved files
            parts = [types.Part(text=msg.content)]
            for file_obj in file_objects:
                parts.append(types.Part.from_uri(
                    file_uri=file_obj.uri,
                    mime_type=file_obj.mime_type
                ))
            api_history.append(types.Content(role=msg.role, parts=parts))

        # --- Call the API ---
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=800
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