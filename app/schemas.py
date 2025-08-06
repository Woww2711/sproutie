# In app/schemas.py

from pydantic import BaseModel
from typing import Optional, List

# --- PLACEHOLDER: This schema will be used later for history ---
# For now, it defines the structure we will eventually expect.
class HistoryMessage(BaseModel):
    role: str
    content: str
# ----------------------------------------------------------------

# This defines the simple request body our gateway API will accept.
class GatewayRequest(BaseModel):
    message: str
    sub_content: Optional[str] = None # Optional field for 'subContent'
    # --- PLACEHOLDER: We include the field but won't use it yet ---
    history: List[HistoryMessage] = []

# This is a helper schema to parse the JSON response from the external server.
class ExternalAIResponse(BaseModel):
    response: str
    follow_up_questions: List[str]

# This defines the final, user-friendly response our gateway API will return.
class GatewayResponse(BaseModel):
    response_text: str
    suggested_prompts: List[str] = []
    # --- PLACEHOLDER: We include the field but it will be empty for now ---
    history: List[HistoryMessage] = []