# In app/services/gateway_service.py

import httpx
from typing import List, Optional
import base64
import hmac
import hashlib
import time
from app.schemas import ExternalAIResponse, HistoryMessage
from dotenv import load_dotenv
import os
import json

load_dotenv()  # Load environment variables from .env file

# --- Configuration ---
# The URL of the external server we are calling.
# It's good practice to put this in one place.


def hash_hmac_sha512(value_to_hash: int, secret_key: Optional[str] = None) -> str:
    value_bytes = str(value_to_hash).encode('utf-8')
    secret_bytes = secret_key.encode('utf-8') if secret_key else b''

    hmac_obj = hmac.new(secret_bytes, value_bytes, hashlib.sha512)
    return base64.b64encode(hmac_obj.digest()).decode('utf-8')

EXTERNAL_API_URL = "http://192.168.31.5:3001/now/v1/ai/gemini" # e.g., "https://generativelanguage.googleapis.com/..."

def load_system_prompt():
    """Reads the system prompt content from the markdown file."""
    try:
        with open("sproutie_system_prompt.md", "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: sproutie_system_prompt.md not found. Using a default prompt.")
        return "You are a helpful plant assistant."

SYSTEM_PROMPT = load_system_prompt()

# This is our main service function.
async def call_external_api(
    message: str,
    sub_content: str | None,
    history: List[HistoryMessage] # We accept history, but ignore it for now
) -> ExternalAIResponse:
    """
    Constructs the request payload and calls the external AI server.
    """
    # 1. Construct the 'content' string with the system prompt and user message.
    # In the future, we will inject the 'history' into this string as well.
    content_payload = (
        f"--- SYSTEM PROMPT ---\n{SYSTEM_PROMPT}\n"
        f"--- USER QUERY ---\n{message}"
    )

    # 2. Define the full JSON body for the external API.
    # This structure matches the 'curl' command you provided.
    json_payload = {
        "content": content_payload,
        "subContent": sub_content or "", # Use sub_content or a default
        "stream": False,
      "generationConfig": {
        "responseMimeType": "application/json",
        "responseSchema": {
          "type": "OBJECT",
          "properties": {
            "response": {
              "type": "STRING"
            },
            "follow_up_questions": {
              "type": "ARRAY",
              "items": { "type": "STRING" },
              "minItems": 3,
              "maxItems": 3
            }
          },
          "required": [
            "follow_up_questions",
            "response"
          ],
          "propertyOrdering": ["response", "follow_up_questions"]
        }
      }
    }
    
    time_stamp = int(time.time() * 1000)
    key = hash_hmac_sha512(time_stamp, os.getenv("AES_SECRET_KEY"))
    headers = {
        'TimeStamps': str(time_stamp), 'Key': key, 'Content-Type': 'application/json'
    }

    # 3. Make the asynchronous HTTP request using httpx.
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                EXTERNAL_API_URL,
                json=json_payload,
                headers=headers,
                timeout=30.0 # Set a reasonable timeout
            )
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            # The external API's response might be nested. We need to parse it.
            # Based on the standard Google API, the actual content is in a specific path.
            # We will assume a simple structure first, and can adjust if needed.
            # Let's assume the direct response is the JSON we want.
            response_data = response.json()
            
            try:
            # 1. Get the text content which is a JSON string
              json_string_from_api = response_data['candidates'][0]['content']['parts'][0]['text']
              
              # 2. Parse that inner JSON string
              structured_data = json.loads(json_string_from_api)

              # 3. Validate the parsed data using our Pydantic schema
              return ExternalAIResponse.model_validate(structured_data)

            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
                # This broad exception catches any errors during parsing
                # (e.g., if 'candidates' is missing, is empty, etc.)
                print(f"Error parsing the nested JSON from external API: {e}")
                print(f"Full response received: {response_data}")
                # We must raise an error so the router knows something went wrong.
                raise ValueError("The external AI service returned an unexpected or malformed response.")

        except httpx.HTTPStatusError as e:
            # Re-raise HTTP errors to be handled by the router
            print(f"HTTP Error calling external API: {e.response.text}")
            raise e
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise e