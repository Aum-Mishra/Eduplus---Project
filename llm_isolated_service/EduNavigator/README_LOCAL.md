# EduNavigator - Local Mistral Edition

**Complete AI-powered career guidance running 100% locally - no API keys required!**

## Overview

EduNavigator provides personalized learning roadmaps and career guidance by:
1. **Ingesting** your Roadmap PDFs and Mindmaps
2. **Retrieving** relevant content using vector search (FAISS) + smart ranking (MMR)
3. **Generating** customized roadmaps using **local Mistral LLM** via Ollama

**Key Difference from Original:**
- ✅ **No Google API key needed** - Uses local Mistral LLM  
- ✅ **Completely offline** - All inference on your machine
- ✅ **Fully isolated** - Separate server (port 8010) doesn't affect main system
- ✅ **Safe integration** - No dependencies on Flask, Rasa, or ML models

---

## Prerequisites

### 1. Ollama + Mistral (Required)

EduNavigator needs a local LLM server running. We use **Mistral** via **Ollama**.

**Install Ollama:**
- Download: https://ollama.ai
- Install and run: `ollama serve` (keeps running in background)

**Get Mistral Model:**
```powershell
ollama pull mistral
```

Verify setup:
```powershell
# Check Ollama is running
curl http://localhost:11434/api/tags

# Should show: {"models": [{"name": "mistral:latest", ...}, ...]}
```

### 2. Python 3.10+
EduNavigator runs in its own isolated environment - automatically set up.

### 3. Your PDFs
Place files in the correct directories:
- **Roadmaps:** `llm_isolated_service/EduNavigator/backend/storage/Roadmap_dataset/`
- **Mindmaps:** `llm_isolated_service/EduNavigator/backend/storage/Mindmaps/`

---

## Installation & Setup

### Option A: Full System Setup (Recommended)
Integrates EduNavigator + all other services:

```powershell
# Setup everything (one-time)
.\setup_system.ps1 -SetupOnly

# Start all services
.\setup_system.ps1 -RunOnly
```

This creates:
- `.venv_all` - Shared environment (Flask, Rasa, etc.)
- `.venv_edunavigator_local` - EduNavigator's isolated environment

### Option B: EduNavigator Only
Just run EduNavigator:

```powershell
# Setup
.\start_edunavigator_local.ps1 -SetupOnly

# Start
.\start_edunavigator_local.ps1 -Port 8010
```

---

## Running the System

### Step 1: Start Ollama (if not already running)
```powershell
ollama serve
```
Leave this terminal open. Ollama listens on `http://localhost:11434`.

### Step 2: Start EduNavigator
```powershell
# From project root
.\start_edunavigator_local.ps1
```

**What happens:**
- ✅ Creates isolated Python environment
- ✅ Installs dependencies (no Google API involved)
- ✅ Verifies Ollama is running
- ✅ Starts FastAPI server on port 8010
- ✅ Loads FAISS index from storage

### Step 3: Access the Service

**Swagger API Docs:**
```
http://localhost:8010/docs
```

**Test endpoints directly:**
```powershell
# Health check
curl http://localhost:8010/health

# Build index from PDFs
curl -X POST http://localhost:8010/api/ingest

# Get career roadmap
$body = @{
    profile = @{
        branch = "Computer Science"
        interests = @("Web Development", "AI")
        skills = @("Python", "JavaScript")
        goal = "Become a Full-Stack AI Developer"
    }
} | ConvertTo-Json

curl -X POST http://localhost:8010/api/recommend `
  -ContentType "application/json" `
  -Body $body

# Ask a career question
$body = @{
    question = "What should I learn to get started with machine learning?"
    profile = @{
        branch = "ECE"
        interests = @("AI", "Data Science")
        skills = @("Python", "Mathematics")
        goal = "ML Engineer"
    }
} | ConvertTo-Json

curl -X POST http://localhost:8010/api/ask `
  -ContentType "application/json" `
  -Body $body
```

---

## API Endpoints

### `POST /api/ingest`
Parse PDFs and build FAISS index.

**Response:**
```json
{
  "ok": true,
  "chunks_indexed": 245,
  "message": "Successfully indexed 245 document chunks"
}
```

### `POST /api/recommend`
Generate personalized learning roadmap.

**Request Body:**
```json
{
  "profile": {
    "branch": "Computer Science",
    "interests": ["Web Dev", "AI"],
    "skills": ["Python", "JavaScript"],
    "goal": "Full-Stack Developer"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "plan": {
    "careerPath": "Full-Stack Developer → Cloud Architect",
    "roadmap": [
      {
        "title": "Foundation (Months 1-2)",
        "steps": [
          "Master React & Node.js",
          "Learn Docker & Kubernetes basics",
          "Build 2-3 projects"
        ]
      }
    ],
    "resources": [
      {"title": "React Official Docs", "type": "docs", "url": "..."},
      {"title": "Docker Handbook", "type": "guide"}
    ],
    "projects": [
      "Full-stack todo app with authentication",
      "Multi-service microservices project"
    ]
  },
  "sources": [
    {"source": "roadmap_fullstack.pdf", "section": "Web Tech Stack"},
    {"source": "mindmap_docker.pdf", "section": "Containerization"}
  ]
}
```

### `POST /api/ask`
Answer career guidance questions with context.

**Request Body:**
```json
{
  "question": "How do I prepare for a data science internship?",
  "profile": {
    "branch": "Electronics",
    "interests": ["AI", "Data"],
    "skills": ["Python", "Statistics"],
    "goal": "Data Scientist"
  }
}
```

**Response:**
```json
{
  "ok": true,
  "answer": "Based on your profile and our resources, here's what you should focus on...",
  "sources": [{"source": "career_prep.pdf"}]
}
```

### `GET /api/mindmap?source=example.pdf`
Get mindmap visualization for a document.

### `POST /api/feedback`
Log user interactions for improvement.

---

## Architecture

```
┌─────────────────────────────────────────┐
│   Dashboard (React) @ :5173             │
│   - Navigation to EduNavigator          │
└──────────────┬──────────────────────────┘
               │
               │ http://localhost:8010
               ▼
┌─────────────────────────────────────────┐
│   EduNavigator FastAPI @ :8010          │
│   (Isolated .venv_edunavigator_local)   │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │ RAG Pipeline                    │   │
│   │ - PDF Ingest → Chunks          │   │
│   │ - Embedding (Sentence-Trans)   │   │
│   │ - Vector Storage (FAISS)       │   │
│   │ - Retrieval (MMR + Compress)   │   │
│   └─────────────────┬───────────────┘   │
│                     │                   │
│   ┌─────────────────▼───────────────┐   │
│   │ LLM Generation                  │   │
│   │ - Mistral via HTTP              │   │
│   │ - Prompt engineering            │   │
│   │ - JSON parsing                  │   │
│   └─────────────────┬───────────────┘   │
└─────────────────────┼───────────────────┘
                      │ http://localhost:11434
                      ▼
                  ┌───────────┐
                  │ Ollama    │
                  │ Mistral   │
                  │ (Local)   │
                  └───────────┘
```

**Completely Isolated From:**
- ✅ Flask (port 5000) - No shared dependencies
- ✅ Rasa (ports 5005, 5055) - No chatbot interference  
- ✅ ML Models - No prediction pipeline conflicts
- ✅ LLM Service (port 8001) - Separate generation backend

---

## Configuration

Edit `backend/.env.local` to customize:

```env
# Ollama endpoint
OLLAMA_URL=http://localhost:11434

# Server settings
EDUNAVIGATOR_PORT=8010
EDUNAVIGATOR_HOST=0.0.0.0

# Embedding model (sentence-transformers)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Retrieval settings
TOP_K=6              # Top documents returned
FETCH_K=20           # Initial fetch size
MMR_LAMBDA=0.5       # MMR diversity parameter

# Data paths
STORAGE_DIR=./storage
DATA_ROADMAP_DIR=./storage/Roadmap_dataset
DATA_MINDMAP_DIR=./storage/Mindmaps
```

---

## Troubleshooting

### "Cannot connect to Ollama"
```powershell
# Check Ollama is running
ollama serve

# Or check if it's already running
netstat -ano | findstr :11434
```

### "Mistral not found"
```powershell
# Pull the model
ollama pull mistral

# Verify
ollama list
```

### "FAISS index not found"
```powershell
# Rebuild index from PDFs
curl -X POST http://localhost:8010/api/ingest

# Ensure PDFs are in correct directories
# - backend/storage/Roadmap_dataset/
# - backend/storage/Mindmaps/
```

### "Slow responses"
- Increase Ollama memory if available
- Reduce `TOP_K` in .env for fewer retrieved documents
- Ensure no other heavy processes are running

### Service won't start
1. Check Python 3.10 is available: `py -3.10 --version`
2. Check virtual environment: `.venv_edunavigator_local/Scripts/python.exe`
3. Check dependencies: `pip list | findstr faiss`
4. Check logs in terminal output

---

## Integration with Main System

EduNavigator is integrated into the main Dashboard:

**Frontend (UI Eduplus/src/app/components/Dashboard.tsx):**
- Added sidebar navigation link
- Opens EduNavigator in new tab
- Button redirects to `http://localhost:8010`

**System Setup (setup_system.ps1):**
- Calls `start_edunavigator_local.ps1 -SetupOnly` during setup
- Launches EduNavigator on port 8010 during runtime
- Completely separate from Flask, Rasa, and LLM services

**Independence:**
```
✅ Own Python virtual environment (.venv_edunavigator_local)
✅ Own server process (isolated terminal)
✅ Own dependencies (FAISS, LangChain, Sentence Transformers)
✅ Own port (8010)
✅ Own storage (backend/storage/)
✅ Own configuration (.env.local)
```

No changes needed to Flask, Rasa, or main LLM service.

---

## Advanced Features

### Custom Ollama Models
Switch to different local models:

```powershell
# Download other models
ollama pull llama2
ollama pull neural-chat

# Update .env.local
# OLLAMA_MODEL=neural-chat
```

Then modify `generation_local.py`:
```python
self.model = "neural-chat"  # Change model name
```

### Prompt Customization
Edit system prompts in `generation_local.py`:

```python
SYSTEM_PROMPT = (
    "You are EduNavigator, an expert career guide. "
    "..."
)
```

### Performance Tuning
In `.env.local`:
```env
TOP_K=3          # Fewer documents = faster
FETCH_K=10       # Smaller initial pool
MMR_LAMBDA=0.3   # More similarity (less diversity)
```

---

## File Structure

```
llm_isolated_service/EduNavigator/
├── backend/
│   ├── main_local.py              ← Entry point (LOCAL VERSION)
│   ├── .env.local                 ← Configuration (NO GOOGLE KEY)
│   ├── requirements.txt           ← Updated (no google-generativeai)
│   ├── rag/
│   │   ├── generation_local.py    ← Mistral adapter (NEW)
│   │   ├── retrieval.py           ← FAISS search (unchanged)
│   │   ├── ingest.py              ← PDF ingestion (unchanged)
│   │   └── embeddings.py          ← Sentence transformers (unchanged)
│   └── storage/
│       ├── Roadmap_dataset/       ← Your PDFs here
│       ├── Mindmaps/              ← Your mindmaps here
│       └── faiss_index/           ← Built index (auto-created)
├── README.md                      ← This file
└── start_edunavigator_local.ps1   ← Launcher script (NEW)
```

---

## What's Different from Original?

| Feature | Original | Local Edition |
|---------|----------|---------------|
| LLM | Google Gemini API | Mistral (Ollama) |
| API Key | Required | Not needed |
| Offline | No | Yes ✅ |
| Cost | Free tier limited | Free ✅ |
| Speed | API latency | Local latency ✅ |
| Privacy | Data sent to Google | Local only ✅ |
| Setup | Complex (.env setup) | Simple (one script) |

---

## Performance Notes

**Response Times:**
- **Ingest** (245 PDFs): 2-5 minutes (first time)
- **Recommendation**: 15-30 seconds (with Mistral inference)
- **Q&A**: 10-25 seconds (with context retrieval)

**Memory Usage:**
- Ollama + Mistral: ~5-7 GB RAM
- EduNavigator service: ~1-2 GB RAM
- FAISS index: ~500 MB (varies with PDFs)

**Optimization Tips:**
- Run Ollama on a dedicated GPU for 3-4x speedup
- Use smaller `TOP_K` for faster responses
- Pre-warm Ollama by running a test request

---

## Next Steps

1. **Ensure Ollama is running:** `ollama serve`
2. **Ensure Mistral is downloaded:** `ollama pull mistral`
3. **Place your PDFs** in `backend/storage/Roadmap_dataset/` and `backend/storage/Mindmaps/`
4. **Start EduNavigator:** `.\start_edunavigator_local.ps1`
5. **Ingest PDFs:** POST `http://localhost:8010/api/ingest`
6. **Get roadmaps:** POST `http://localhost:8010/api/recommend`

---

## Support

- **API Documentation:** http://localhost:8010/docs
- **Main System:** http://localhost:5173
- **Ollama Docs:** https://ollama.ai
- **Mistral Model:** https://mistral.ai

**Completely safe, locally-run career guidance! 🚀**
