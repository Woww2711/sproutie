# In app/main.py
from fastapi import FastAPI
from .routers import gateway_router

app = FastAPI(
    title="AI Sproutie API",
    description="AI Sproutie virtual assistant.",
    version="1.0.0"
)

app.include_router(gateway_router.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the AI Sproutie! 🌱"}