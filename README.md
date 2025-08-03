
# 🌱 AI Sproutie - Plant Care Assistant (API Only)

AI Sproutie is a FastAPI backend for plant identification, diagnosis, and care advice. It supports multimodal chat (text + image) and conversation history, powered by Google Gemini. **This branch exposes only the FastAPI backend (no Gradio UI).**



## Features
- Multimodal chat: text and image support
- Plant identification and diagnosis
- Conversation history (stateful)
- Ready-to-integrate FastAPI backend


sproutie-api-project/

## Project Structure
```
sproutie-api-project/
├── requirements.txt            # Python dependencies
├── sproutie_system_prompt.md   # AI system prompt
└── app/
    ├── main.py                # FastAPI app
    ├── schemas.py             # Pydantic schemas
    ├── routers/
    │   └── chat.py            # Chat API endpoints
    └── services/
        └── gemini_service.py  # Gemini API logic
```

## 🚀 Quickstart

```bash
git clone <your-repository-url>
cd sproutie-api-project
conda create --name sproutie-api python=3.11 -y
conda activate sproutie-api
pip install -r requirements.txt
```

1. Add your Gemini API key to a `.env` file:
   ```env
   GEMINI_API_KEY="YOUR_API_KEY_HERE"
   ```
2. Ensure `sproutie_system_prompt.md` is present in the root directory.

## ▶️ Running

```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for the FastAPI interactive docs.


## 🌐 API Endpoints

### POST `/v1/chat`
**Type:** `multipart/form-data`

**Fields:**
- `api_key` (str, required)
- `message` (str, required)
- `user_id` (str, optional)
- `history` (str, required, JSON array)
- `image` (file, optional)

### GET `/api/v1/chat/history`
**Query:**
- `user_id` (str, required)
- `session_id` (int, required)

---



## 💻 API Usage Examples (curl)

> For best results, use Linux/macOS or Git Bash on Windows. Do **not** manually set the Content-Type header.

### 1. Send a Message with an Image
```bash
curl -X POST "http://127.0.0.1:8000/v1/chat" \
  -H "accept: application/json" \
  -F "api_key=YOUR_GEMINI_API_KEY" \
  -F "message=What is this plant?" \
  -F "history=[]" \
  -F "image=@/path/to/your/plant.jpg"
```

### 2. Send a Follow-up Message (with History)
Copy the `history` array from the previous response and use it as the value for the next turn:
```bash
curl -X POST "http://127.0.0.1:8000/v1/chat" \
  -H "accept: application/json" \
  -F "api_key=YOUR_GEMINI_API_KEY" \
  -F "message=How much water does it need?" \
  -F "history=[{\"role\":\"user\",\"content\":\"What is this plant?\",\"file_references\":[{\"name\":\"files/abc-123\",\"mime_type\":\"image/jpeg\"}]},{\"role\":\"model\",\"content\":\"That is a Monstera Deliciosa!\"}]"
```
