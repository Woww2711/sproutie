# In app/main.py
from fastapi import FastAPI
from .routers import chat

app = FastAPI(
    title="AI Sproutie Stateless API",
    description="A stateless API for the AI Sproutie virtual assistant.",
    version="1.0.0"
)

app.include_router(chat.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the AI Sproutie API! 🌱"}