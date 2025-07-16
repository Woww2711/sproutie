from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatRequest, ChatResponse
from app import models, database

# Create a new router object
router = APIRouter(
    prefix="/v1/chat",
    tags=["Chat"]
)

# Dependency to get a database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ChatResponse)
async def handle_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Handles a user's chat message, managing the session and conversation history.
    """
    # Step 1: Find or create the chat session
    session_id = request.session_id
    if not session_id:
        # Create a new session
        new_session = models.ChatSession(user_id=request.user_id)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
    else:
        # Verify the session exists (optional but good practice)
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
        if not db_session:
            # Handle error: session not found
            # For simplicity, we'll just create a new one for now.
            new_session = models.ChatSession(user_id=request.user_id, id=session_id)
            db.add(new_session)
            db.commit()
            db.refresh(new_session)

    # Step 2: Save the user's message to the database
    user_message = models.ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message,
        # image_url will be handled later
    )
    db.add(user_message)
    db.commit()

    # Step 3: Get conversation history (we'll use this in the next step with Gemini)
    history = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at).all()
    
    # --- Placeholder for Gemini API Call ---
    # We will replace this with a real call to the Gemini API soon.
    # For now, we'll create a dummy assistant response.
    
    assistant_response_text = f"Sproutie has received {len(history)} message(s) in this session. Your last message was: '{request.message}'"
    
    # Step 4: Save the assistant's response to the database
    assistant_message = models.ChatMessage(
        session_id=session_id,
        role="assistant",
        content=assistant_response_text
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        response_text=assistant_response_text,
        suggested_prompts=["How do I repot this?", "Is this plant toxic to cats?"]
    )