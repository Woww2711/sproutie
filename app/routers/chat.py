from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatRequest, ChatResponse
from app import models, database
from app.services import gemini_service # <-- Import our new service

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
    Handles a user's chat message, managing session and calling the AI model.
    """
    session_id = request.session_id
    db_session = None
    if session_id:
        db_session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()

    if not db_session:
        db_session = models.ChatSession(user_id=request.user_id, id=session_id)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    
    session_id = db_session.id

    # Save the user's message
    user_message = models.ChatMessage(
        session_id=session_id, role="user", content=request.message
    )
    db.add(user_message)
    db.commit()

    # Get conversation history (excluding the message just added)
    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session_id
    ).order_by(models.ChatMessage.created_at).all()
    
    # --- THIS IS THE UPDATED PART ---
    # Call the Gemini Service to get the AI's response
    assistant_response_text = await gemini_service.get_chat_response(
        history=history
    )
    # --- END OF UPDATED PART ---

    # Save the assistant's response
    assistant_message = models.ChatMessage(
        session_id=session_id, role="assistant", content=assistant_response_text
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        session_id=session_id,
        response_text=assistant_response_text,
        # We can have Gemini generate these in the future
        suggested_prompts=[] 
    )