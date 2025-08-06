# In app/routers/gateway_router.py

from fastapi import APIRouter, HTTPException, status, Form
from typing import Optional
from app.schemas import GatewayResponse, HistoryMessage
from app.services import gateway_service, history_service

router = APIRouter(
    prefix="/v1/gateway",
    tags=["Stateful Gateway Chat"]
)

@router.post("/", response_model=GatewayResponse)
async def handle_stateful_gateway_chat(
    # We now accept user_id and an optional session_id
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[int] = Form(None),
    sub_content: Optional[str] = Form(None)
):
    """
    Handles a stateful chat request, managing history on the server's filesystem.
    """
    # 1. Determine the session ID
    if session_id is None:
        # If no session ID is provided, create a new one
        current_session_id = await history_service.get_next_session_id(user_id)
    else:
        current_session_id = session_id

    # 2. Get the history for this conversation
    current_history = await history_service.get_history(user_id, current_session_id)

    # 3. Call the external API with the message and its context
    try:
        external_response = await gateway_service.call_external_api(
            message=message,
            sub_content=sub_content,
            history=current_history
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error with external AI service: {e}"
        )

    # 4. Update the history with the new turn
    current_history.append(HistoryMessage(role="user", content=message))
    current_history.append(HistoryMessage(role="model", content=external_response.response))
    
    # 5. Save the updated history back to the file
    await history_service.save_history(user_id, current_session_id, current_history)

    # 6. Return the response to the client
    return GatewayResponse(
        response_text=external_response.response,
        suggested_prompts=external_response.follow_up_questions,
        user_id=user_id,
        session_id=current_session_id
    )