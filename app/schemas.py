# In app/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List

# This represents a single message in the conversation history
# that the client will send to us.
class HistoryMessage(BaseModel):
    role: str # "user" or "model"
    content: str

# This is our new main request body.
# We no longer use form-data, so we're back to a JSON body.
class StatelessChatRequest(BaseModel):
    user_id: str = "postman-user" # Still useful for logging/tracking
    message: str
    history: List[HistoryMessage] = [] # The client sends the history
    api_key: str = Field(..., description="The user's Google Gemini API Key.")

# This is the response from our service to our router.
# It remains unchanged.
class GeminiServiceResponse(BaseModel):
    response_text: str
    input_tokens: int
    output_tokens: int

# This is the final response sent back to the user/Postman.
# It also remains largely unchanged.
class ChatResponse(BaseModel):
    response_text: str
    history: List[HistoryMessage] = []
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None