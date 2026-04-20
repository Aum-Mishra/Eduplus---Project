# EduPlus Project

EduPlus is an integrated placement intelligence platform that combines ML prediction, company analytics, chatbot assistance (Rasa + isolated LLM), and a React frontend for students.

## What You Get
- Placement probability prediction from student profile data
- Salary prediction and threshold probabilities
- Predicted role + recommended companies
- Low-probability action reports with practical improvement guidance
- Company policy/intelligence Q&A (package, CGPA, skills, rounds)
- LeetCode company question analytics with PDF export
- Student-facing web UI for prediction and report download

## Repository Structure
- app.py: Main Flask backend APIs
- modules/: Feature engineering, ML models, and probability utilities
- data/: Student/company datasets and generated outputs
- models/: Trained model artifacts
- Chatbot/: Rasa chatbot configuration, actions, and models
- llm_isolated_service/: Separate LLM chatbot backend
- UI Eduplus/: React + Vite frontend

## Unified Dependency File
Use this file for Python dependencies across backend, chatbot, ML, and LLM components:
- requirements.common.txt

## Quick Start (Windows)

### 1. Prerequisites
- Python 3.10.x (important for Rasa compatibility)
- Node.js + npm
- (Optional) Ollama if using isolated LLM local model flow

### 2. Setup + Run Everything
From project root:

```powershell
.\setup_system.ps1
```

Other modes:

```powershell
.\setup_system.ps1 -SetupOnly
.\setup_system.ps1 -RunOnly
```

## Service Endpoints (Typical)
- Main Flask API: http://localhost:5000
- Rasa API: http://localhost:5005
- Rasa Action Server: http://localhost:5055
- Isolated LLM API: http://localhost:8001
- Frontend (Vite dev): usually http://localhost:5173

## Detailed Documentation
For full architecture, feature behavior, and workflow details:
- INFO.md

## Notes
- Python and Node dependency ecosystems are intentionally separate.
- Keep large generated files/models under control for manageable Git history.
- If models are missing, setup script auto-trains required artifacts where possible.

## License
Add your preferred license here (MIT/Apache-2.0/etc.).
