# In app/main.py

from fastapi import FastAPI
from .routers import chat
from .database import engine, Base

# --- Database Initialization on Startup ---
# When Uvicorn runs this app, it will create the tables.
Base.metadata.create_all(bind=engine)

# --- FastAPI App Definition ---
app = FastAPI(
    title="AI Sproutie API",
    description="The API for the AI Sproutie virtual assistant.",
    version="0.1.0"
    # We can have the docs enabled again, as it's a separate server
)

# Include the chat router
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def read_root():
    """
    A simple welcome message to confirm the API is running.
    """
    return {"message": "Welcome to the AI Sproutie API! 🌱"}