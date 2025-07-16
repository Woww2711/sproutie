from fastapi import APIRouter
from app.schemas import ChatRequest, ChatResponse
import uuid

# Create a new router object
router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest):
    """
    Handles a user's chat message.

    - **user_id**: The unique identifier for the user.
    - **session_id**: The ID of the ongoing conversation. If null, a new session is created.
    - **message**: The text message from the user.
    - **image_base64**: Optional Base64-encoded string of an image.
    """
    # If no session_id is provided, create a new one.
    session_id = request.session_id or str(uuid.uuid4())

    # --- Placeholder Logic ---
    # In the future, this is where we will:
    # 1. Save the user message to the database.
    # 2. Construct the prompt for Gemini.
    # 3. Call the Gemini API.
    # 4. Save the assistant's response.
    # 5. Return the real response.
    
    # For now, we just echo back the user's message.
    response_text = f"Sproutie received your message: '{request.message}'"
    
    return ChatResponse(
        session_id=session_id,
        response_text=response_text,
        suggested_prompts=["What is this plant?", "My plant's leaves are yellow."]
    )