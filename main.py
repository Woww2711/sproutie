from fastapi import FastAPI

# Create an instance of the FastAPI class
app = FastAPI(
    title="AI Sproutie API",
    description="The API for the AI Sproutie virtual assistant.",
    version="0.1.0",
)

# Define a "route" or "endpoint" for the root URL
@app.get("/")
def read_root():
    """
    This is the root endpoint of the API.
    It's a simple welcome message to confirm the API is running.
    """
    return {"message": "Welcome to the AI Sproutie API! 🌱"}