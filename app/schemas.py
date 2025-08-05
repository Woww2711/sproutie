# In app/schemas.py

from pydantic import BaseModel
from typing import Optional, List

# No longer need FileReference, so it's removed.

# HistoryMessage is now text-only.
class HistoryMessage(BaseModel):
    role: str
    content: str

# GeminiServiceResponse is still the same, as it deals with the AI's response.
class GeminiServiceResponse(BaseModel):
    response_text: str
    follow_ups: List[str] = []
    input_tokens: int
    output_tokens: int

# ChatResponse is still the same, but its history will be text-only.
class ChatResponse(BaseModel):
    response_text: str
    history: List[HistoryMessage] = []
    suggested_prompts: List[str] = []
    
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

# AIResponse schema for structured output remains the same.
class AIResponse(BaseModel):
    response: str
    follow_up_questions: List[str]