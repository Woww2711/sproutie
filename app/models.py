import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

from .database import Base

# SQLAlchemy model for the ChatSession table
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
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

    # This creates the "many-to-one" side of the relationship.
    session = relationship("ChatSession", back_populates="messages")