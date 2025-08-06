# In app/services/history_service.py

import aiofiles
import json
import os
from typing import List
from app.schemas import HistoryMessage

HISTORY_DIR = "conversation_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

def _get_filepath(user_id: str, session_id: int) -> str:
    """Constructs the filename for a given conversation."""
    return os.path.join(HISTORY_DIR, f"{user_id}_session_{session_id}.json")

async def get_history(user_id: str, session_id: int) -> List[HistoryMessage]:
    """Reads and parses a conversation history file."""
    filepath = _get_filepath(user_id, session_id)
    if not os.path.exists(filepath):
        return [] # Return empty list if it's a new conversation
    
    async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
        content = await f.read()
        data = json.loads(content)
        # The file stores {"messages": [...]}, we return the list.
        return [HistoryMessage(**msg) for msg in data.get("messages", [])]

async def save_history(user_id: str, session_id: int, history: List[HistoryMessage]):
    """Saves the full conversation history to a file."""
    filepath = _get_filepath(user_id, session_id)
    # Convert Pydantic models to dictionaries for JSON serialization
    history_dicts = [msg.model_dump() for msg in history]
    # Wrap it in the specified format
    data_to_save = {"messages": history_dicts}
    
    async with aiofiles.open(filepath, mode='w', encoding='utf-8') as f:
        await f.write(json.dumps(data_to_save, indent=2))

async def get_next_session_id(user_id: str) -> int:
    """Finds the next available session ID for a user."""
    max_id = 0
    prefix = f"{user_id}_session_"
    for filename in os.listdir(HISTORY_DIR):
        if filename.startswith(prefix) and filename.endswith(".json"):
            try:
                # Extract the number part from the filename
                session_num_str = filename[len(prefix):-len(".json")]
                session_num = int(session_num_str)
                if session_num > max_id:
                    max_id = session_num
            except (ValueError, IndexError):
                continue # Ignore malformed filenames
    return max_id + 1