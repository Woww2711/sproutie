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
def chat_with_sproutie(message: str, chat_history: list, image_input: str, user_id: str, session_id: str):
    user_id_to_use = user_id.strip() if user_id and user_id.strip() else DEFAULT_USER_ID
    
    session_id_to_use = session_id.strip() if session_id and session_id.strip() else None

    if image_input:
        chat_history.append([(image_input,), None])

    form_data = {"user_id": user_id_to_use, "message": message}
    if session_id_to_use:
        form_data["session_id"] = session_id_to_use
        
    files = {}
    if image_input:
        filename = os.path.basename(image_input)
        file_handle = open(image_input, 'rb')
        files['image'] = (filename, file_handle, 'image/jpeg')
    
    try:
        response = requests.post(API_URL, data=form_data, files=files)
        response.raise_for_status()
        
        api_response_data = response.json()
        new_session_id = api_response_data.get("session_id")
        
        chat_history.append([message, api_response_data.get('response_text')])
        
        return "", chat_history, new_session_id

    except requests.exceptions.RequestException as e:
        error_message = f"Error: Could not connect to API. Details: {e}"
        chat_history.append([message, error_message])
        return "", chat_history, session_id_to_use
    finally:
        if 'image' in files:
            files['image'][1].close()

def load_history_from_api(user_id: str, session_id: str):
    user_id_update = gr.update()
    session_id_update = gr.update()

    if not user_id.strip():
        gr.Warning("User ID cannot be empty.")
        return [], gr.update(label="❌ User ID Required"), session_id_update
    if not session_id.strip():
        gr.Warning("Session ID cannot be empty.")
        return [], user_id_update, gr.update(label="❌ Session ID Required")

    try:
        params = {"user_id": user_id.strip(), "session_id": int(session_id.strip())}
        response = requests.get(f"{API_URL}/history", params=params)

        if response.status_code == 404:
            error_detail = response.json().get('detail', 'Not found.')
            gr.Error(error_detail)
            if "User ID" in error_detail:
                return [], gr.update(label=f"❌ User Not Found"), session_id_update
            elif "Session ID" in error_detail:
                return [], gr.update(label="User ID"), gr.update(label=f"❌ Session Not Found")
        
        response.raise_for_status()
        
        data = response.json()
        gradio_history = []
        user_msg = None
        for message in data.get("messages", []):
            if message['role'] == 'user':
                user_msg = message['content']
            elif message['role'] == 'assistant' and user_msg is not None:
                gradio_history.append([user_msg, message['content']])
                user_msg = None
        
        gr.Info("History loaded successfully!")
        # On success, return the new history and reset both labels
        return gradio_history, gr.update(label="User ID"), gr.update(label="Session ID")

    except ValueError:
        gr.Error("Session ID must be a number.")
        return [], user_id_update, gr.update(label="❌ Must be a number")
    except requests.exceptions.RequestException:
        gr.Error("Could not connect to the API.")
        return [], user_id_update, session_id_update


# --- Gradio UI Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🌱 AI Sproutie Chatbot")
    
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(label="Conversation with Sproutie", height=550)
            
            with gr.Row():
                message_input = gr.Textbox(
                    show_label=False, placeholder="Type a message or upload an image...", scale=4
                )
                submit_button = gr.Button("Send", variant="primary", scale=1)

        with gr.Column(scale=1):
            image_input = gr.Image(type="filepath", label="Upload Image")
            
            user_id_input = gr.Textbox(label="User ID", value=DEFAULT_USER_ID)

            with gr.Row():
                session_id_input = gr.Textbox(label="Session ID", placeholder="Enter # to load", scale=3)
                load_button = gr.Button("Load", scale=1)

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
    load_button.click(
        fn=load_history_from_api,
        inputs=[user_id_input, session_id_input],
        outputs=[chatbot, user_id_input, session_id_input]
    )
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