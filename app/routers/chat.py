from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from typing import Optional
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
async def handle_chat(
    # The order doesn't matter, but dependencies often go first
    db: Session = Depends(get_db),
    # These are now Form fields instead of JSON fields
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    # This is how you declare a file upload
    image: Optional[UploadFile] = File(None)
):
    """
    Handles a user's chat message, now accepting form-data and an optional image.
    """
    
    # --- Step 1: Find or Create the Chat Session (Same as before) ---
    db_session = None
    if session_id:
        try:
            sequence_num = int(session_id)
            db_session = db.query(models.ChatSession).filter(
                models.ChatSession.user_id == user_id,
                models.ChatSession.user_session_sequence == sequence_num
            ).first()
        except (ValueError, TypeError):
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID must be a valid integer."
            )
    if not db_session:
        max_sequence = db.query(func.max(models.ChatSession.user_session_sequence)).filter(
            models.ChatSession.user_id == user_id
        ).scalar() or 0
        new_sequence_num = max_sequence + 1
        db_session = models.ChatSession(
            user_id=user_id, user_session_sequence=new_sequence_num
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
    
    internal_session_id = db_session.id
    external_session_id = str(db_session.user_session_sequence)

    # --- Step 2: Handle File Upload (NEW LOGIC) ---
    new_uploaded_file_api_name = None
    if image:
        
        # Upload the file to the Gemini Files API via our service
        gemini_file = await gemini_service.upload_file_to_gemini(
            file=image
        )
        
        if gemini_file:
            # If upload was successful, save the reference to our database
            db_uploaded_file = models.UploadedFile(
                session_id=internal_session_id,
                file_api_name=gemini_file.name, # e.g., "files/abc-123"
                # display_name=image.filename
            )
            db.add(db_uploaded_file)
            new_uploaded_file_api_name = gemini_file.name
        else:
            # Handle upload failure
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image to external service."
            )

    # --- Step 3: Save User Message (Same as before) ---
    user_message = models.ChatMessage(
        session_id=internal_session_id, role="user", content=message
    )
    db.add(user_message)
    
    # We commit both the user message and the file upload reference at the same time
    db.commit()

    # --- Step 4: Prepare data for Gemini (MODIFIED LOGIC) ---
    # Get all chat messages for the session
    history = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == internal_session_id
    ).order_by(models.ChatMessage.created_at).all()
    
    # Get all uploaded file API names for the session
    session_files = db.query(models.UploadedFile.file_api_name).filter(
        models.UploadedFile.session_id == internal_session_id
    ).all()
    # The query returns a list of tuples, so we extract the first element of each
    file_api_names = [file[0] for file in session_files]
    
    # --- Step 5: Call Gemini Service (we need to update the service next) ---
    service_response = await gemini_service.get_chat_response(
        history=history,
        file_api_names=file_api_names
    )

    # --- Step 6: Save and Return Response (Same as before) ---
    assistant_message = models.ChatMessage(
        session_id=internal_session_id,
        role="assistant",
        content=service_response.response_text,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens
    )
    db.add(assistant_message)
    db.commit()

    return ChatResponse(
        session_id=external_session_id,
        response_text=service_response.response_text,
        input_tokens=service_response.input_tokens,
        output_tokens=service_response.output_tokens,
        total_tokens=service_response.input_tokens + service_response.output_tokens
    )