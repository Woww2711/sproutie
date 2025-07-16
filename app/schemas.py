from pydantic import BaseModel
from typing import Optional, List

# Pydantic model for the request body of the chat endpoint
class ChatRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    message: str
    image_base64: Optional[str] = None

# Pydantic model for the response body of the chat endpoint
class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    suggested_prompts: List[str] = []