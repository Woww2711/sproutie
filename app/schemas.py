# In app/schemas.py

from pydantic import BaseModel
from typing import Optional, List

# This represents a single message in the conversation history.
# It's used for both parsing the input history string and building the output history.
class HistoryMessage(BaseModel):
    role: str # "user" or "model"
    content: str
    image_base64: Optional[str] = None

# We no longer need a Pydantic model for the main request, as it will be form-data.

# This is the response from our service to our router. Unchanged.
class GeminiServiceResponse(BaseModel):
    response_text: str
    input_tokens: int
    output_tokens: int

# This is the final JSON response sent back to the user/Postman. Unchanged.
class ChatResponse(BaseModel):
    response_text: str
    history: List[HistoryMessage] = []
    
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None