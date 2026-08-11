# EduPlus Isolated LLM Chatbot Service

This is a fully separate chatbot service that runs in parallel with the existing Rasa system.

## What this service does
- Uses local Mistral (via Ollama) for conversational responses
- Keeps student-specific chat history and sessions
- Reads student/prediction/company data from existing CSV files
- Handles company intelligence and placement insights
- Supports LeetCode company-wise question retrieval and PDF report generation
- Exposes a separate API surface, without changing the existing backend server

## Important
- Existing Rasa chatbot remains untouched.
- Existing `app.py` remains untouched for this LLM service.
- This service runs on a separate port and separate endpoints.

## Prerequisites
1. Ollama installed and running
2. Local model available (default: `mistral`)

Example:
```powershell
ollama list
ollama run mistral
```

## Setup
```powershell
cd llm_isolated_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run
```powershell
cd llm_isolated_service
.\.venv\Scripts\Activate.ps1
python app.py
```

Default URL: `http://localhost:8001`

## Main Endpoints
- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/student/<student_id>`
- `GET /api/llm-chat-history/<student_id>`
- `POST /api/llm-chat-history/<student_id>/new`
- `DELETE /api/llm-chat-history/<student_id>/<chat_id>`
- `DELETE /api/llm-chat-history/<student_id>`
- `POST /api/llm-chatbot/message`
- `GET /api/llm-reports/<filename>`

## Optional Env Vars
- `LLM_OLLAMA_BASE_URL` (default: `http://localhost:11434`)
- `LLM_MODEL_NAME` (default: `mistral`)
- `LLM_SERVER_PORT` (default: `8001`)

## LLM Auditor Tool
The tool at `tools/llm_question_auditor.py` can validate responses against the existing `CHATBOT_QUESTION_CATALOG.md`.
