# 🌱 AI Sproutie - Stateful Gateway API

Welcome to the `text-only-api` branch of the AI Sproutie project. This version of the application is a **Stateful Gateway API**, designed to provide a simple, user-friendly interface that communicates with a more complex external AI service.

It intelligently manages conversation history on the server-side using a local file system, allowing clients to have continuous, multi-turn conversations without needing to manage the history themselves.

## 🏛️ Architectural Overview

This API acts as a "smart proxy" or gateway. The data flow is designed for simplicity on the client-side and power on the backend.

```
+-----------+       +-------------------------+       +--------------------+
|           |-----> |                         |-----> |                    |
|  Client   |       |   Our Gateway API       |       |   External AI      |
| (Postman) | <-----|   (FastAPI on server)   | <-----|   Server           |
|           |       |                         |       |                    |
+-----------+       +-----------+-------------+       +--------------------+
                                |
                                | Manages State
                                V
                        +-----------------+
                        |                 |
                        |  File System    |
                        | (.json history) |
                        +-----------------+
```

1.  **Client:** The client (e.g., Postman, a future mobile app) only needs to know the `user_id` and the current `session_id`.
2.  **Gateway API:** Our FastAPI application receives the simple request. It is responsible for:
    *   Looking up the conversation history from a local JSON file.
    *   Constructing the complex, detailed prompt required by the external AI server (including system prompts, history, and the new message).
    *   Calling the external server.
    *   Parsing the complex response.
    *   Saving the updated conversation history back to the file.
    *   Returning a simple, clean response to the client.
3.  **External AI Server:** The powerful, upstream service that handles the core AI logic.
4.  **File System:** Acts as our simple "database" for storing conversation state.

## ✨ Key Features

- **Server-Side State Management:** The API handles conversation history automatically. Clients only need to pass a `session_id` to continue a conversation.
- **Simplified Interface:** Exposes a clean and simple endpoint, hiding the complexity of the upstream AI service.
- **New Session Creation:** Automatically creates a new conversation session for a user if no `session_id` is provided.
- **Structured AI Responses:** Leverages the external API's ability to generate structured JSON, providing not just a text response but also suggested follow-up questions.
- **Asynchronous & Performant:** Built with FastAPI and `httpx` for modern, non-blocking I/O.
- **File-Based History:** Uses a simple, human-readable file system approach for storing conversation logs, perfect for demos and smaller-scale applications.

## 🛠️ Tech Stack

- **Backend Framework:** Python, FastAPI
- **HTTP Client:** `httpx` (for async requests to the external server)
- **Asynchronous File I/O:** `aiofiles`
- **Data Validation:** Pydantic
- **History Storage:** Local JSON files

## 📁 Project Structure

The project is organized for clarity, separating concerns into different modules.

```
sproutie-api-project/
├── .gitignore
├── conversation_history/   # Auto-generated folder for storing .json logs
├── requirements.txt        # Python package dependencies
├── sproutie_system_prompt.md # The core personality and instruction prompt
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI app definition and root endpoint
    ├── schemas.py          # Pydantic data validation schemas
    ├── routers/
    │   └── gateway_router.py # The single API endpoint for the gateway
    └── services/
        ├── gateway_service.py # Logic for calling the external AI server
        └── history_service.py # Logic for reading/writing history files
```

## 🚀 Setup and Installation

### 1. Clone the Repository & Checkout Branch

```bash
git clone <your-repository-url>
cd sproutie-api-project
git checkout text-only-api
```

### 2. Set Up Conda Environment

```bash
conda create --name sproutie-api python=3.11 -y
conda activate sproutie-api
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the External API Endpoint

You must specify the URL of the external server you are calling.

1.  Open the file `app/services/gateway_service.py`.
2.  Find the line `EXTERNAL_API_URL = "YOUR_EXTERNAL_API_ENDPOINT_HERE"`.
3.  Replace the placeholder URL with the actual, valid endpoint URL.

## ▶️ Running the Application

To run the FastAPI server, execute the following command from the project's root directory:

```bash
uvicorn app.main:app --reload
```

The server will start on `http://127.0.0.1:8000`. The `conversation_history/` directory will be created automatically if it doesn't exist.

## 🔬 API Endpoint & Usage Guide

The API exposes a single, powerful endpoint for all chat interactions.

### Endpoint: `POST /v1/gateway`

This endpoint handles all chat messages. Its behavior changes based on the provided `session_id`.

-   **If `session_id` is OMITTED:** A new conversation is started for the given `user_id`, and a new `session_id` is created and returned.
-   **If `session_id` is PROVIDED:** The existing conversation for that `user_id` and `session_id` is loaded from the server's history and continued.

#### Request (`multipart/form-data`)

| Key          | Type    | Required | Description                                                                                              |
| :----------- | :------ | :------- | :------------------------------------------------------------------------------------------------------- |
| `user_id`    | string  | **Yes**  | A unique identifier for the user (e.g., "user-123").                                                     |
| `message`    | string  | **Yes**  | The text message from the user.                                                                          |
| `session_id` | integer | No       | The ID of the conversation to continue. If omitted, a new conversation is started.                       |
| `sub_content`| string  | No       | An optional string that is passed to the `subContent` field of the external API.                         |

#### Response (`application/json`)

```json
{
  "response_text": "Yellow leaves with brown spots on a Monstera often point to overwatering...",
  "suggested_prompts": [
    "How can I check for root rot?",
    "What does a fungal infection look like?",
    "How much light does my Monstera need?"
  ],
  "user_id": "user-123",
  "session_id": 1
}
```

### Postman Workflow Example

#### Turn 1: Starting a New Conversation

1.  Set the request type to `POST` and the URL to `http://127.0.0.1:8000/v1/gateway`.
2.  Go to the **Body** tab and select **`form-data`**.
3.  Add two key-value pairs:
    *   `user_id`: `user-123`
    *   `message`: `Hello, Sproutie!`
4.  Send the request.
5.  The response will contain the AI's answer and a new `session_id` (e.g., `1`).

#### Turn 2: Continuing the Conversation

1.  Keep the same request open.
2.  Add a third key-value pair:
    *   `session_id`: `1` (Use the ID from the previous response).
3.  Change the `message` to your follow-up question (e.g., `Tell me about Monstera plants.`).
4.  Send the request. The API will now load the history of session `1` and continue the conversation.

## 💾 How State Management Works

This API is stateful from the user's perspective but achieves this without a traditional database.

-   **Storage:** All conversations are stored in the `conversation_history/` directory.
-   **Filename:** Each conversation has a unique filename based on the user and session: `{user_id}_session_{session_id}.json`. (e.g., `user-123_session_1.json`).
-   **File Content:** Each JSON file contains a single object with a `messages` key, which holds an array of all turns in that conversation.

**Example `user-123_session_1.json`:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, Sproutie!"
    },
    {
      "role": "model",
      "content": "Hello there! I'm AI Sproutie, your friendly plant assistant. How can I help you today? 🌱"
    },
    {
      "role": "user",
      "content": "Tell me about Monstera plants."
    },
    {
      "role": "model",
      "content": "Of course! The Monstera deliciosa, or Swiss Cheese Plant, is famous for its beautiful, split leaves..."
    }
  ]
}
```
