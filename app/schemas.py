# In app/schemas.py

from pydantic import BaseModel
from typing import Optional, List

# This is a helper for our history files and for the gateway service.
class HistoryMessage(BaseModel):
    role: str
    content: str

# This helper is for parsing the response from the external AI server.
class ExternalAIResponse(BaseModel):
    response: str
    follow_up_questions: List[str]

# This is the final, simple response our API will send back to the client.
# Note: It does NOT contain the history.
class GatewayResponse(BaseModel):
    response_text: str
    suggested_prompts: List[str] = []
    user_id: str
    session_id: int # We return the session ID for the client to use next time