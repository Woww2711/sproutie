import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

from .database import Base

# SQLAlchemy model for the ChatSession table
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)

    user_session_sequence = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # This creates a "one-to-many" relationship.
    # One session can have many messages.
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# SQLAlchemy model for the ChatMessage table
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    input_tokens = Column(Integer, nullable=True, default=0)
    output_tokens = Column(Integer, nullable=True, default=0)

    # This creates the "many-to-one" side of the relationship.
    session = relationship("ChatSession", back_populates="messages")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    
    # The name returned by the Gemini Files API (e.g., "files/abc-123-xyz")
    file_api_name = Column(String, unique=True, nullable=False, index=True)
    
    # # The original filename from the user (e.g., "my_monstera.jpg")
    # display_name = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    session = relationship("ChatSession")