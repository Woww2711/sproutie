# 🌱 AI Sproutie - Your Personal Plant Care Assistant

AI Sproutie is a smart, friendly, and empathetic virtual assistant designed to help you care for your plants with confidence. Built with a powerful backend and a user-friendly demo interface, Sproutie can identify plants, diagnose problems, and provide expert care advice through a natural, conversational chat.

This repository contains the full source code for the FastAPI backend API and the Gradio frontend demo.


![alt text](image.png)

## ✨ Features

- **Multimodal Chat:** Converse with Sproutie using both text and images.
- **Plant Identification:** Upload a photo of a plant, and Sproutie will do its best to identify it.
- **Problem Diagnosis:** Describe symptoms or show a picture of a sick plant to get potential diagnoses and solutions.
- **Stateful Conversations:** Sproutie remembers the context of your conversation, including previously uploaded images, within a single session.
- **Conversation History:** Load and review past conversations by providing a User ID and Session ID.
- **Interactive UI:** A simple and intuitive Gradio demo interface for easy interaction and demonstration.
- **Robust Backend:** A scalable API built with FastAPI, ready for integration into a mobile or web app.

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Frontend / UI:** Gradio
- **AI Model:** Google Gemini API (`gemini-2.5-flash-lite-preview-06-17`)
- **Database:** SQLAlchemy with SQLite
- **Deployment Model:** Optimized for Hugging Face Spaces (Threaded FastAPI + Gradio)

## 📁 Project Structure

The project is organized into two main parts: the FastAPI application (`app/`) and the Gradio UI (`app.py`).

```
sproutie-api-project/
├── .gitignore
├── app.py              # Main entry point for Gradio UI and server logic
├── requirements.txt    # Python package dependencies
├── sproutie_system_prompt.md # The core personality and instruction prompt for the AI
└── app/
    ├── __init__.py
    ├── database.py     # SQLAlchemy setup (engine, session)
    ├── main.py         # FastAPI app definition and root endpoint
    ├── models.py       # SQLAlchemy database table models
    ├── schemas.py      # Pydantic data validation schemas
    ├── routers/
    │   └── chat.py     # API routes for all chat-related endpoints
    └── services/
        └── gemini_service.py # Logic for interacting with the Google Gemini API
```

## 🚀 Setup and Installation

Follow these steps to get the application running on your local machine.

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd sproutie-api-project
```

### 2. Set Up Conda Environment

It is highly recommended to use a virtual environment.

```bash
# Create a new conda environment with Python 3.11
conda create --name sproutie-api python=3.11 -y

# Activate the environment
conda activate sproutie-api
```

### 3. Install Dependencies

Install all the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

You need to provide your Google Gemini API key.

1.  Create a file named `.env` in the root of the project directory.
2.  Add your API key to this file:

    ```env
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```
    *(The `.gitignore` file is already configured to ignore this file, keeping your key secure.)*

### 5. System Prompt

Make sure the `sproutie_system_prompt.md` file is present in the root directory. This file defines the AI's personality, expertise, and rules of engagement.

## ▶️ Running the Application

To run the complete application (both the FastAPI backend and the Gradio UI), execute the following command from the root directory:

```bash
python app.py
```

This will:
1.  Create the `sproutie.db` SQLite database file if it doesn't exist.
2.  Start the FastAPI server in a background thread on `http://127.0.0.1:8000`.
3.  Launch the Gradio web interface, which you can access at **`http://127.0.0.1:7860`**.

Open `http://127.0.0.1:7860` in your web browser to start chatting with Sproutie!

## 🌐 API Endpoints

The FastAPI backend exposes the following endpoints, running at `http://127.0.0.1:8000`.

<details>
<summary><strong>API Endpoint Details</strong></summary>

- **`POST /api/v1/chat`**
  - **Type:** `multipart/form-data`
  - **Description:** Handles a chat message, including optional image uploads. Manages session creation and state.
  - **Form Fields:**
    - `user_id` (str, required)
    - `message` (str, required)
    - `session_id` (str, optional)
    - `image` (file, optional)

- **`GET /api/v1/chat/history`**
  - **Type:** Query Parameters
  - **Description:** Retrieves the full message history for a specific conversation.
  - **Query Parameters:**
    - `user_id` (str, required)
    - `session_id` (int, required)

</details>

## 🤗 Deploying to Hugging Face Spaces

This project is structured for easy deployment to Hugging Face Spaces.

1.  Create a new Space on Hugging Face.
2.  Choose **Gradio** as the SDK.
3.  Link it to your GitHub repository or upload the files manually.
4.  Go to the **Settings** tab of your new Space.
5.  Navigate to **Repository secrets** and add a new secret:
    - **Name:** `GEMINI_API_KEY`
    - **Secret value:** Paste your actual Google Gemini API key here.
6.  The Space will build automatically using the `app.py` entry point and `requirements.txt` file.

## 🔮 Future Improvements

- **Streaming Responses:** Implement response streaming to make the chatbot feel more interactive and "live".
- **AI-Generated Suggestions:** Prompt the AI to suggest relevant follow-up questions to guide the user.
- **Full User Authentication:** Replace the simple `user_id` string with a proper JWT-based authentication system for a production app.
- **Dockerization:** Create a `Dockerfile` to containerize the application for deployment on other cloud platforms.