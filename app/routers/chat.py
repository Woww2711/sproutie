# In app/routers/chat.py

from fastapi import APIRouter, HTTPException, status
from app.schemas import StatelessChatRequest, ChatResponse, HistoryMessage
from app.services import gemini_service

router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

@router.post("/", response_model=ChatResponse)
async def handle_stateless_chat(request: StatelessChatRequest):
    """
    Handles a single, stateless chat request and returns the
    full updated conversation history.
    """
    try:
        service_response = await gemini_service.get_stateless_chat_response(
            history=request.history,
            new_message=request.message,
            api_key=request.api_key
        )

        # --- THIS IS THE NEW LOGIC ---
        
        # 1. Create the new, updated history list
        updated_history = request.history  # Start with the history the user sent us
        
        # 2. Add the user's latest message
        updated_history.append(
            HistoryMessage(role="user", content=request.message)
        )
        
        # 3. Add the new AI response
        updated_history.append(
            HistoryMessage(role="model", content=service_response.response_text)
        )

        # 4. Prepare and return the final response, including the new history
        return ChatResponse(
            response_text=service_response.response_text,
            history=updated_history, # Include the full history
            input_tokens=service_response.input_tokens,
            output_tokens=service_response.output_tokens,
            total_tokens=service_response.input_tokens + service_response.output_tokens
        )

    except Exception as e:
        # Catch errors from the service (e.g., invalid API key, network issues)
        # and return a proper HTTP error.
        # This is a generic catch-all. We can make it more specific if needed.
        error_detail = str(e)
        if "API key not valid" in error_detail:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your Google Gemini API key is not valid. Please check it and try again."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {error_detail}"
        )