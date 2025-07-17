import os
from dotenv import load_dotenv
from typing import List
from fastapi import UploadFile
import google.genai as genai
from google.genai import types
from app import models
from app.schemas import GeminiServiceResponse
import asyncio

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

async def upload_file_to_gemini(
    file: UploadFile
) -> types.File:
    """
    Uploads a FastAPI UploadFile object to the Gemini Files API.

    Args:
        file: The UploadFile object directly from the FastAPI request.

    Returns:
        The File object returned by the API.
    """
    if not client:
        print("Error: Gemini client is not configured for file upload.")
        return None
    
    try:
        print(f"Uploading file '{file.filename}' to Gemini Files API...")
        # THE FIX: We pass the .file attribute of the UploadFile object directly.
        # We also pass the display_name in the 'config' parameter.
        uploaded_file = await client.aio.files.upload(
            file=file.file,
            config=types.UploadFileConfig(
                # display_name=file.filename,
                mime_type=file.content_type
            )
        )
        print(f"Successfully uploaded file. API Name: {uploaded_file.name}")
        return uploaded_file
        
    except Exception as e:
        print(f"An error occurred during file upload to Gemini: {e}")
        return None

async def get_chat_response(
    history: List[models.ChatMessage], 
    session_files: List[tuple[str, str]]
) -> GeminiServiceResponse:
    """
    Gets a response from the Gemini API, using the correct object types for history.
    """
    if not client:
        return GeminiServiceResponse(
            response_text="Error: Gemini client is not configured.",
            input_tokens=0, output_tokens=0
        )

    # --- CORRECTED PROMPT CONSTRUCTION ---
    
    # 1. Build the chat history using the SDK's 'types.Content' object
    api_history = []
    for msg in history[:-1]: # Go through all messages EXCEPT the last one
        api_role = 'model' if msg.role == 'assistant' else 'user'
        # THE FIX: Create a types.Content object instead of a dictionary
        api_history.append(types.Content(
            role=api_role, 
            parts=[types.Part(text=msg.content)]
        ))
    
    file_api_names = [file[0] for file in session_files]
    try:
        get_file_tasks = [client.aio.files.get(name=name) for name in file_api_names]
        file_objects = await asyncio.gather(*get_file_tasks)
    except Exception as e:
        print(f"Error retrieving files from Gemini API: {e}")
        # Handle case where a file might have expired or been deleted
        return GeminiServiceResponse(
            response_text="I couldn't seem to find one of the files we were talking about. It might have expired (I can only remember files for 48 hours). Could you upload it again?",
            input_tokens=0, output_tokens=0
        )

    # 3. Construct the final user prompt with the latest text and ALL file objects
    last_user_message = history[-1].content
    final_prompt_parts = [types.Part(text=last_user_message)]
    # Add the retrieved File objects directly to the parts list
    for file_obj in file_objects:
        mime_type = next((mime for name, mime in session_files if name == file_obj.name), "image/jpeg")
        final_prompt_parts.append(
            types.Part.from_uri(
                file_uri=file_obj.uri, 
                mime_type=mime_type # Use the dynamic mime_type
            )
        )

    api_history.append(types.Content(role='user', parts=final_prompt_parts))
    
    try:
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=api_history, # Pass the list of Content objects
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
        return GeminiServiceResponse(
            response_text="Oh no! My digital roots are tangled. I couldn't process that. Please try again. 😵‍💫",
            input_tokens=0,
            output_tokens=0
        )