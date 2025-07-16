from fastapi import FastAPI
from app.routers import chat
from .database import engine, Base # <-- ADD THIS IMPORT

# Create all database tables
# This line looks at all the classes that inherit from Base (in models.py)
# and creates the corresponding tables in the database.
Base.metadata.create_all(bind=engine) # <-- ADD THIS LINE

# Create an instance of the FastAPI class
app = FastAPI(
    title="AI Sproutie API",
    description="The API for the AI Sproutie virtual assistant. This API manages chat sessions and interacts with a generative AI model to provide plant care support.",
    version="0.1.0",
)

# Include the chat router
# All endpoints from the chat router will be added to the main app
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def read_root():
    """
    This is the root endpoint of the API.
    It's a simple welcome message to confirm the API is running.
    """
    return {"message": "Welcome to the AI Sproutie API! 🌱"}