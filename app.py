# In app.py

import gradio as gr
import requests
import threading
import uvicorn
import time
import os

# --- Backend Imports ---
from app.main import app as fastapi_app
from app.database import engine, Base

# --- Configuration ---
API_URL = "http://127.0.0.1:8000/v1/chat"
DEFAULT_USER_ID = "demo-user-123" # A default value for the user ID field

# --- Database Initialization ---
def create_db_and_tables():
    print("Creating database and tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

# --- UI Logic ---
# The function now takes user_id and session_id from the UI
def chat_with_sproutie(message: str, chat_history: list, image_input: str, user_id: str, session_id: str):
    # If the user_id from the UI is empty, use the default.
    user_id_to_use = user_id.strip() if user_id and user_id.strip() else DEFAULT_USER_ID
    
    # Session ID from the UI can be None or an empty string, which is fine.
    session_id_to_use = session_id.strip() if session_id and session_id.strip() else None

    if image_input:
        # Add a turn that is just the user's image. The bot response is None.
        chat_history.append([(image_input,), None])

    # 2. Prepare the API call (this part doesn't change)
    form_data = {"user_id": user_id_to_use, "message": message}
    if session_id_to_use:
        form_data["session_id"] = session_id_to_use
        
    files = {}
    if image_input:
        filename = os.path.basename(image_input)
        # We need to re-open the file since the previous history append might have used it.
        # It's safer to just handle the file once for the request.
        file_handle = open(image_input, 'rb')
        files['image'] = (filename, file_handle, 'image/jpeg')
    
    try:
        response = requests.post(API_URL, data=form_data, files=files)
        response.raise_for_status()
        
        api_response_data = response.json()
        new_session_id = api_response_data.get("session_id")
        
        # 3. Add the user's text message and the bot's response
        chat_history.append([message, api_response_data.get('response_text')])
        
        return "", chat_history, new_session_id

    except requests.exceptions.RequestException as e:
        error_message = f"Error: Could not connect to API. Details: {e}"
        chat_history.append([message, error_message])
        return "", chat_history, session_id_to_use
    finally:
        if 'image' in files:
            # files['image'][1] is the file_handle
            files['image'][1].close()

# --- Gradio UI Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌱 AI Sproutie Demo")
    
    with gr.Row():
        # This column will contain the main chat components
        with gr.Column(scale=4): # Make this main column wider
            chatbot = gr.Chatbot(label="Conversation with Sproutie", height=550)
            
            with gr.Row():
                message_input = gr.Textbox(
                    show_label=False, placeholder="Type a message or upload an image...", scale=4
                )
                submit_button = gr.Button("Send", variant="primary", scale=1)

        # This column will be a narrow sidebar for the image and session info
        with gr.Column(scale=1): # Make this sidebar column narrower
            image_input = gr.Image(type="filepath", label="Upload Image")
            
            with gr.Row():
                user_id_input = gr.Textbox(label="User ID", value=DEFAULT_USER_ID)
                session_id_input = gr.Textbox(label="Session ID", placeholder="Starts new session if empty")
    # -----------------------

    # Define the event handler for the button click
    submit_button.click(
        fn=chat_with_sproutie,
        inputs=[message_input, chatbot, image_input, user_id_input, session_id_input],
        outputs=[message_input, chatbot, session_id_input]
    )
    message_input.submit(
        fn=chat_with_sproutie,
        inputs=[message_input, chatbot, image_input, user_id_input, session_id_input],
        outputs=[message_input, chatbot, session_id_input]
    )
    # Clear the image input after submission
    submit_button.click(lambda: None, None, image_input, queue=False)
    message_input.submit(lambda: None, None, image_input, queue=False)


# --- Main Execution ---
def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    create_db_and_tables()
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    time.sleep(2) 
    demo.launch()