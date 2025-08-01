# In app/routers/chat.py

from fastapi import APIRouter, HTTPException, status, Form, File, UploadFile
from typing import Optional, List, Union
from app.schemas import ChatResponse, HistoryMessage
from app.services import gemini_service
import json
import pydantic

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

@router.post("/", response_model=ChatResponse)
async def handle_multimodal_chat(
    # --- The endpoint signature remains multipart/form-data ---
    api_key: str = Form(...),
    message: str = Form(...),
    user_id: str = Form("postman-user"),
    history: str = Form("[]"), 
    image: Union[Optional[UploadFile], str] = File(None)
):
    """
    Handles a multimodal chat request. Accepts an optional image and a
    JSON string for history, using the Gemini Files API for efficient
    image handling.
    """
    # 1. Parse and Validate the incoming history string
    try:
        history_data = json.loads(history)
        validated_history = pydantic.parse_obj_as(List[HistoryMessage], history_data)
    except (json.JSONDecodeError, pydantic.ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid 'history' format. Must be a JSON string of an array. Error: {e}"
        )

    # 2. Upload the new image, if it exists, to get a file reference
    new_file_references: List[str] = []
    if image:
        try:
            # Call the upload service
            uploaded_file = await gemini_service.upload_file_to_gemini(
                file=image, 
                api_key=api_key
            )
            # Store the reference name
            new_file_references.append(uploaded_file.name)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File upload failed: {e}")
        finally:
            await image.close()

    # 3. Construct the history for this turn, including the new message and file reference
    # This becomes the last item in the list sent to the main service.
    current_turn_history = validated_history
    current_turn_history.append(
        HistoryMessage(
            role="user", 
            content=message, 
            file_references=new_file_references if new_file_references else None
        )
    )

    # 4. Call the main service with the complete history
    try:
        service_response = await gemini_service.get_multimodal_chat_response(
            history=current_turn_history,
            api_key=api_key,
        )
    except Exception as e:
        error_detail = str(e)
        if "API key not valid" in error_detail:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google Gemini API key.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"API Error: {error_detail}")

    # 5. Build the final response, including the AI's response turn
    final_history = current_turn_history
    final_history.append(
        HistoryMessage(role="model", content=service_response.response_text)
    )

    return ChatResponse(
        response_text=service_response.response_text,
        history=final_history,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens,
        total_tokens=service_response.input_tokens + service_response.output_tokens
    )