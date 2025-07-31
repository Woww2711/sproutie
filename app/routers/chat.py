# In app/routers/chat.py

from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile
from typing import Optional, List, Union
from app.schemas import ChatResponse, HistoryMessage
from app.services import gemini_service
import json
import pydantic
import base64

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

@router.post("/", response_model=ChatResponse)
async def handle_multipart_chat(
    # --- New signature with Form and File ---
    api_key: str = Form(...),
    message: str = Form(...),
    user_id: str = Form("postman-user"),
    # History is now a string, which we expect to be a JSON array.
    # It defaults to an empty JSON array string '[]'.
    history: str = Form("[]"), 
    image: Union[Optional[UploadFile], str] = File(None)
):
    """
    Handles a chat request via multipart/form-data, with an optional
    image and a JSON string for history.
    """
    # --- Parse and Validate Inputs ---
    
    # 1. Parse the history JSON string
    try:
        history_data = json.loads(history)
        # Use Pydantic to validate the structure of the parsed history
        validated_history = pydantic.parse_obj_as(List[HistoryMessage], history_data)
    except (json.JSONDecodeError, pydantic.ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 'history' format. It must be a valid JSON string of an array of objects. Error: {e}"
        )

    # 2. Process the image file into a Base64 string, if it exists
    image_b64_string: Optional[str] = None
    if image:
        try:
            image_bytes = await image.read()
            image_b64_string = base64.b64encode(image_bytes).decode("utf-8")
        finally:
            await image.close()
            
    # --- Call the Service (No changes needed here) ---
    try:
        service_response = await gemini_service.get_stateless_chat_response(
            history=validated_history,
            new_message=message,
            api_key=api_key,
            new_image_b64=image_b64_string
        )
    except Exception as e:
        # ... (error handling for Gemini API) ...
        error_detail = str(e)
        if "API key not valid" in error_detail:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google Gemini API key.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"API Error: {error_detail}")

    # --- Build the Response (No changes needed here) ---
    updated_history = validated_history
    updated_history.append(HistoryMessage(role="user", content=message, image_base64=image_b64_string))
    updated_history.append(HistoryMessage(role="model", content=service_response.response_text))

    return ChatResponse(
        response_text=service_response.response_text,
        history=updated_history,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens,
        total_tokens=service_response.input_tokens + service_response.output_tokens
    )