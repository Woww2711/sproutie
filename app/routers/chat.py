from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    Handles a user's chat message.
    If session_id is provided, it must be the user-facing sequence number (e.g., 1, 2, 3).
    """
    db_session = None

    if request.session_id:
        try:
            # The session_id from the user is now the sequence number
            sequence_num = int(request.session_id)
            # Find the session for this user with this sequence number
            db_session = db.query(models.ChatSession).filter(
                models.ChatSession.user_id == request.user_id,
                models.ChatSession.user_session_sequence == sequence_num
            ).first()
        except (ValueError, TypeError):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID must be a valid integer."
            )

    # If no session was found (either because ID was null or didn't exist)
    if not db_session:
        # --- THIS IS THE NEW LOGIC ---
        # Find the highest existing sequence number for this user
        max_sequence = db.query(func.max(models.ChatSession.user_session_sequence)).filter(
            models.ChatSession.user_id == request.user_id
        ).scalar() or 0
        
        # The new sequence number is the next one in line
        new_sequence_num = max_sequence + 1
        
        # Create the new session object
        db_session = models.ChatSession(
            user_id=request.user_id,
            user_session_sequence=new_sequence_num
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    
    # The internal session_id is the UUID
    internal_session_id = db_session.id
    # The external session_id is the sequence number
    external_session_id = str(db_session.user_session_sequence)

    # Save the user's message
    user_message = models.ChatMessage(
        session_id=internal_session_id, role="user", content=request.message
    )
    db.add(user_message)
    db.commit()

    # Get conversation history
    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == internal_session_id
    ).order_by(models.ChatMessage.created_at).all()
    
    # 1. Call the Gemini Service, which now returns a structured object
    service_response = await gemini_service.get_chat_response(history=history)

    # 2. Save the assistant's response WITH token data to the database
    assistant_message = models.ChatMessage(
        session_id=internal_session_id,
        role="assistant",
        content=service_response.response_text,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens
    )
    db.add(assistant_message)
    db.commit()

    # 3. Prepare the final API response WITH token data for the client
    return ChatResponse(
        session_id=external_session_id,
        response_text=service_response.response_text,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens,
        total_tokens=service_response.input_tokens + service_response.output_tokens,
        suggested_prompts=[]
    )