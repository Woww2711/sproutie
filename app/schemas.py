# In app/schemas.py

from pydantic import BaseModel
from typing import Optional, List

# This represents a single message turn in the conversation history.
# It now contains a list of file names (references) instead of image data.
class HistoryMessage(BaseModel):
    role: str
    content: str
    file_references: Optional[List[str]] = None

# This is the response from our service to our router. Unchanged.
class GeminiServiceResponse(BaseModel):
    response_text: str
    input_tokens: int
    output_tokens: int

# This is the final JSON response sent back to the user/Postman.
# Its 'history' field will use the updated HistoryMessage schema.
class ChatResponse(BaseModel):
    response_text: str
    history: List[HistoryMessage] = []
    
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None