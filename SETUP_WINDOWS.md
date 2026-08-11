# EduPlus Windows Setup

This repository runs as one EduPlus system on one Windows PC with three isolated Python virtual environments.

## Prerequisites

- Python 3.10 installed and available through `py -3.10`
- Node.js and npm installed
- Windows PowerShell
- Internet access for the first dependency install

Python 3.13 may still exist globally on the machine, but EduPlus uses the Python 3.10 environments created by the setup script.

## Why Three Virtual Environments

EduPlus separates incompatible dependency trees so they do not fight each other:

- Backend venv for Flask + ML packages
- Rasa venv for Rasa and custom actions
- RAG venv for FastAPI + LangChain + FAISS + Sentence Transformers + Gemini

This avoids the Rasa and LangChain/Pydantic conflict that happens when everything is installed together.

## First-Time Setup

Run this once from the project root:

```powershell
.\setup_all.ps1
```

This will:

- verify Python 3.10
- verify Node/npm
- create `.venv_backend`, `.venv_rasa`, and `.venv_rag`
- upgrade pip in each environment
- install the split requirements files
- install the React frontend dependencies
- train a Rasa model only if one does not already exist
- validate the backend, Rasa, RAG, and Node setup

## Start the Full System

After setup, start every service with one command:

```powershell
.\start_all.ps1
```

Services started:

- Flask backend: `http://localhost:5000`
- React frontend: `http://localhost:5173`
- Rasa: `http://localhost:5005`
- Rasa Actions: `http://localhost:5055`
- RAG: `http://localhost:8001`

## Stop the Full System

```powershell
.\stop_all.ps1
```

This stops only the EduPlus processes launched by `start_all.ps1`.

## Check Service Health

```powershell
.\check_services.ps1
```

Expected output:

- `[OK] Flask :5000`
- `[OK] React :5173`
- `[OK] Rasa :5005`
- `[OK] Actions :5055`
- `[OK] RAG :8001`

## Manual Service Commands

### Backend

```powershell
.\.venv_backend\Scripts\python.exe app.py
```

### Rasa Action Server

```powershell
cd Chatbot
..\.venv_rasa\Scripts\rasa.exe run actions --enable-api --cors * --port 5055
```

### Rasa Webhook Server

```powershell
cd Chatbot
..\.venv_rasa\Scripts\rasa.exe run --enable-api --cors * --port 5005
```

### RAG FastAPI Service

```powershell
cd llm_isolated_service\EduNavigator\backend
..\..\..\.venv_rag\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

### React Frontend

```powershell
cd "UI Eduplus"
npm run dev
```

## Environment Variables

The RAG service uses the Google Gemini API key from the environment.
Do not commit secrets.

Important variables used by the codebase include:

- `BACKEND_API_URL`
- `RASA_WEBHOOK_URL`
- `RASA_URL`
- `VITE_API_URL`
- `VITE_LLM_API_URL`
- `VITE_EDUNAVIGATOR_URL`
- `GOOGLE_API_KEY`
- `LLM_OLLAMA_BASE_URL`
- `LLM_MODEL_NAME`

## Troubleshooting

- If `py -3.10` fails, install Python 3.10 and retry.
- If the Rasa model is missing, rerun `setup_all.ps1` so the model is trained once.
- If a port is already in use, stop the existing EduPlus process before starting again.
- If Gemini access fails, verify `GOOGLE_API_KEY` is set for the RAG environment.
- If Node modules are missing, rerun `setup_all.ps1` or run `npm install` inside `UI Eduplus`.

## Recommended Workflow

First time:

```powershell
.\setup_all.ps1
```

Every time after that:

```powershell
.\start_all.ps1
```

Stop:

```powershell
.\stop_all.ps1
```

Check:

```powershell
.\check_services.ps1
```
