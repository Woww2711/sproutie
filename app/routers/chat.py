# In app/routers/chat.py

from fastapi import APIRouter, HTTPException, status, Form
from typing import Optional, List
from app.schemas import ChatResponse, HistoryMessage
from app.services import gemini_service
import json
import pydantic

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

@router.post("/", response_model=ChatResponse)
async def handle_text_chat(
    # --- The signature no longer accepts a File ---
    api_key: str = Form(...),
    message: str = Form(...),
    user_id: str = Form("postman-user"),
    history: str = Form("[]"), 
):
    """
    Handles a text-only chat request via multipart/form-data.
    """
    # 1. Parse and Validate the incoming history string (no change here)
    try:
        history_data = json.loads(history)
        validated_history = pydantic.parse_obj_as(List[HistoryMessage], history_data)
    except (json.JSONDecodeError, pydantic.ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 'history' format. Must be a JSON string of an array. Error: {e}"
        )

    # 2. Image upload logic has been completely removed.

    # 3. Construct the history for this turn
    history_for_service = validated_history
    history_for_service.append(
        HistoryMessage(role="user", content=message) # No file_references field
    )

    # 4. Call the main service (we will update this next)
    try:
        service_response = await gemini_service.get_text_chat_response(
            history=history_for_service,
            api_key=api_key,
        )
    except Exception as e:
        error_detail = str(e)
        if "API key not valid" in error_detail:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google Gemini API key.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"API Error: {error_detail}")

    # 5. Build the final history for the response
    final_history = history_for_service
    final_history.append(
        HistoryMessage(role="model", content=service_response.response_text)
    )

    # 6. Return the complete response
    return ChatResponse(
        response_text=service_response.response_text,
        history=final_history,
        suggested_prompts=service_response.follow_ups,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens,
        total_tokens=service_response.input_tokens + service_response.output_tokens
    )