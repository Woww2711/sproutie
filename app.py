# In app.py (at the root of your project)

import os
import gradio as gr
import requests
import threading
import uvicorn
import time

# --- Backend Imports ---
from app.main import app as fastapi_app  # Import the FastAPI app instance
from app.database import engine, Base    # Import for startup table creation

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/v1/chat"
USER_ID = "demo-user-huggingface"

# --- Database Initialization ---
def create_db_and_tables():
    print("Creating database and tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

# --- UI Logic (using Requests, like your working example) ---
def chat_with_sproutie(message: str, chat_history: list, image_input):
    session_id = None
    if chat_history:
        for turn in reversed(chat_history):
            assistant_msg = turn[1]
            if assistant_msg and "SESSION_ID:" in assistant_msg:
                # Find the session_id we sneakily attached to the response
                session_id = assistant_msg.split("SESSION_ID:")[1].strip().split("]")[0]
                break

    # Prepare form data and files for the multipart request
    form_data = {
        "user_id": USER_ID,
        "message": message,
    }
    if session_id:
        form_data["session_id"] = session_id
        
    files = {}
    if image_input:
        filename = os.path.basename(image_input)
        files['image'] = (filename, open(image_input, 'rb'), 'image/jpeg')
    
    try:
        # Make the API call to our own backend
        response = requests.post(API_URL, data=form_data, files=files)
        response.raise_for_status()
        
        api_response_data = response.json()
        new_session_id = api_response_data.get("session_id")
        
        # Add the new messages to the chat history
        chat_history.append([message, f"{api_response_data.get('response_text')}\n\n[SESSION_ID:{new_session_id}]"])
        # Return an empty string to clear the textbox and the updated history
        return "", chat_history

    except requests.exceptions.RequestException as e:
        error_message = f"Error: Could not connect to API. Details: {e}"
        chat_history.append([message, error_message])
        return "", chat_history
    finally:
        # Important: close the file handle if it was opened
        if 'image' in files:
            files['image'][1].close()


# --- Gradio UI Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌱 AI Sproutie Demo")
    
    chatbot = gr.Chatbot(label="Conversation with Sproutie", height=500)
    
    with gr.Row():
        message_input = gr.Textbox(
            show_label=False, placeholder="Type a message or upload an image...", scale=4
        )
        image_input = gr.Image(type="filepath", label="Upload Image", scale=1)

    submit_button = gr.Button("Send", variant="primary")

    # Define the event handler for the button click
    submit_button.click(
        fn=chat_with_sproutie,
        inputs=[message_input, chatbot, image_input],
        outputs=[message_input, chatbot] # Correctly reference the component objects
    )
    # Clear the image input after submission
    submit_button.click(lambda: None, None, image_input, queue=False)


# --- Main Execution: Run FastAPI in a Thread, then Launch Gradio ---
def run_fastapi():
    # This runs the FastAPI app
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Create and run the database tables first
    create_db_and_tables()
    
    # Run the FastAPI server in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()

    # Give the FastAPI server a moment to start up
    time.sleep(2) 
    
    # Launch the Gradio UI
    demo.launch()