# EduPlus — Integrated Placement Intelligence & Career Analytics System

Welcome to **EduPlus**, an end-to-end, AI-powered placement intelligence and candidate assessment platform. EduPlus combines machine learning algorithms, salary tier prediction, candidate profile analytics, dual chatbot intelligence (Rasa NLU + Isolated LLM RAG), and an interactive React web dashboard to empower students and university placement cells.

---

## 🌟 Key Features

### 1. 📊 Placement Probability & Salary Analytics
- **Placement Probability Model:** Evaluates student profile metrics (DSA, Projects, Aptitude, HR score, Resume ATS rating) to estimate overall campus placement likelihood.
- **Salary Tier & Regression Models:** Predicts expected salary package (in LPA) along with probability distributions across compensation brackets (`>2 LPA`, `>5 LPA`, `>10 LPA`, `>15 LPA`, `>20 LPA`, `>30 LPA`, `>40 LPA`).
- **Targeted Action Plans:** Identifies weak areas and generates actionable improvement reports for candidates below target thresholds.

### 2. 🎯 Job Role & Company Matching
- **KNN Company Recommendation Engine:** Recommends top matching hiring companies based on candidate skill profiles and historical campus recruitment data.
- **Role Alignment:** Predicts optimal tech job roles (e.g., Software Development Engineer, Data Analyst, Cloud/DevOps, QA) aligned with student strengths.

### 3. 🤖 Dual-Intelligence Chatbot Ecosystem
- **Rasa NLU Placement Assistant (`/Chatbot`):** Handles company eligibility queries, CGPA criteria, average/highest package information, interview round structures, and backlog policies.
- **Isolated LLM RAG Service (`/llm_isolated_service`):** Interactive AI career guide backed by retrieval-augmented generation for open-ended career query resolution.

### 4. 💻 Skill & Profile Evaluators
- **LeetCode DSA Scorer (`modules/leetcode_dsa.py`):** Fetches real-time profile analytics from LeetCode to compute candidate problem-solving scores.
- **GitHub Project Analyzer (`modules/github_project.py`):** Evaluates candidate repository quality, commit intensity, language diversity, and documentation.
- **HR Round Simulator (`modules/hr_round.py`):** Structured behavioral question evaluation based on communication, ownership, and STAR method compliance.

### 5. 📱 Modern Interactive Dashboard (`/UI Eduplus`)
- Sleek, responsive user interface built with **React**, **TypeScript**, **Vite**, and **Tailwind CSS**.
- Features candidate profile lookups, interactive score input sliders, real-time prediction charts, company intelligence search, and downloadable PDF report generation.

---

## 🏗️ System Architecture

```
                       +-----------------------------------+
                       |      React Web Dashboard          |
                       |    (Vite / React / Tailwind)      |
                       +-----------------+-----------------+
                                         |
                                         v HTTP / REST
                       +-----------------+-----------------+
                       |      Flask Main Backend API       |
                       |           (app.py)                |
                       +--------+--------+--------+--------+
                                |        |        |
         +----------------------+        |        +----------------------+
         |                               v                               |
+--------v-------+              +--------+-------+              +--------v-------+
|  ML Engine &   |              |  Rasa Chatbot  |              | Isolated LLM   |
| Model Binary   |              |   Assistant    |              |  RAG Service   |
| (modules/ &    |              |  (Port 5005 /  |              | (Port 8001 /   |
|  models/*.pkl) |              |   Port 5055)   |              |  EduNavigator) |
+----------------+              +----------------+              +----------------+
```

---

## 🧭 Updated Setup Architecture (Windows)

The recommended Windows setup runs each service in its own isolated virtual environment with clear ports and responsibilities:

```
Windows PC
                │
       ┌───────────┴───────────┐
       │                       │
   Backend venv             RAG venv
       │                       │
   Flask + ML              FastAPI + RAG
       │                       │
      :5000                   :8001
       │
   Rasa venv
       │
   ┌────┴─────┐
   :5005     :5055

       +
   React :5173
```

Summary:
- **Backend venv**: runs Flask API (`app.py`) and ML inference; default port `5000`.
- **RAG venv**: runs the isolated LLM/RAG service (EduNavigator) with FastAPI/Flask; default port `8001`. Uses local Ollama by default.
- **Rasa venv**: runs Rasa HTTP server (`:5005`) and Rasa action server (`:5055`).
- **Frontend**: React (Vite) dev server on `:5173`.

Quick commands (from project root on Windows PowerShell):

```powershell
# Backend venv
python -m venv .venv_backend
.\.venv_backend\Scripts\Activate.ps1
pip install -r requirements.backend.txt
python app.py    # runs on :5000

# RAG venv (LLM service)
python -m venv .venv_rag
.\.venv_rag\Scripts\Activate.ps1
pip install -r llm_isolated_service\requirements.txt
python llm_isolated_service\app.py  # runs on :8001

# Rasa venv
python -m venv .venv_rasa
.\.venv_rasa\Scripts\Activate.ps1
pip install -r requirements.rasa.txt
# in one terminal: rasa run --enable-api --cors "*" --port 5005
# in another:       rasa run actions --port 5055

# Frontend
cd "UI Eduplus"
npm install
npm run dev  # runs on :5173
```

Notes:
- `GOOGLE_API_KEY` is optional — only required if you want to use Google Generative AI (Gemini). The local Ollama flow requires no API key.
- Use `setup_all.ps1` or `start_all.ps1` for automated setup and multi-terminal startup.


## 📁 Repository Directory Structure

```
.
├── app.py                          # Primary Flask API Backend (Endpoints for prediction, chatbots, APIs)
├── main.py                         # Command-line entry point for backend ML pipelines
├── train_models.py                 # Pipeline to train core placement & role ML models
├── train_salary_model.py          # Pipeline to train salary regression & tier models
├── update_profiles.py             # Utility to generate/update candidate profile datasets
├── evaluate_ml_models_report.py    # Model evaluation metrics & validation generator
├── setup_system.ps1               # One-click Windows PowerShell system installer & runner
├── requirements.common.txt         # Consolidated Python dependencies for all backend services
│
├── modules/                        # Core Python Business Logic & Feature Engineering
│   ├── feature_engineering.py     # Data transformation and feature preparation
│   ├── ml_models.py               # ML model loader and inference wrapper
│   ├── salary_probability.py      # Salary tier classification logic
│   ├── service_product_probability.py # Product vs Service company probability breakdown
│   ├── leetcode_dsa.py            # LeetCode GraphQL API integration
│   ├── github_project.py          # GitHub API repository evaluator
│   ├── aptitude_ats.py            # Aptitude & Resume ATS scoring logic
│   └── hr_round.py                # Behavioral HR interview scoring engine
│
├── models/                         # Pre-trained ML Artifacts (.pkl)
│   ├── placement_model.pkl        # RandomForest placement predictor
│   ├── salary_model.pkl           # Salary package regression model
│   ├── salary_tier_model.pkl      # Salary bracket classification model
│   ├── jobrole_model.pkl          # Role recommendation model
│   ├── knn_companies.pkl          # Company nearest-neighbor recommendation model
│   └── *.pkl                      # Scalers, encoders, and feature list artifacts
│
├── data/                           # Datasets & Database CSVs
│   ├── campus_placement_dataset_final_academic_4000.csv # Primary model dataset (4k records)
│   ├── company_placement_db.csv   # Company recruitment criteria database
│   ├── student_profiles_100.csv   # Sample student test dataset
│   └── leetcode-companywise-interview-questions-master/ # LeetCode question bank by company
│
├── Chatbot/                        # Rasa Conversational AI Subsystem
│   ├── domain.yml                 # Rasa domain definition (intents, responses, slots)
│   ├── config.yml                 # Rasa NLU pipeline and policy configuration
│   ├── data/                      # NLU training data, stories, and rules
│   └── actions/                   # Custom Python action server code for DB queries
│
├── llm_isolated_service/           # Isolated LLM Subsystem (EduNavigator RAG)
│   ├── app.py                     # Standalone FastAPI/Flask wrapper for LLM service
│   ├── llm/                       # LLM prompt templates and pipeline handlers
│   └── EduNavigator/              # Source directory for isolated RAG service
│
├── UI Eduplus/                     # Frontend Application
│   ├── src/                       # React components, pages, dashboard, & styles
│   ├── package.json               # Node.js dependencies & scripts
│   └── vite.config.ts             # Vite server & bundler configuration
│
└── Roadmap/                        # Personalized Learning Roadmap Generator
    ├── leetcode_analyzer.py       # Topic gap analysis module
    └── main.py                    # Learning path generator CLI
```

---

## 💻 Tech Stack & Requirements

- **Backend:** Python 3.10+ *(Python 3.10 is recommended for Rasa compatibility)*, Flask, Flask-CORS, Pandas, NumPy, Scikit-learn, Joblib, Requests.
- **Frontend:** Node.js 18+, React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
- **Chatbot & NLP:** Rasa Open Source 3.x, Rasa SDK, Custom NLU actions.
- **LLM Engine:** LangChain / Ollama integration for local RAG deployment.

---

## 🚀 Quick Start Guide (Windows)

### Option 1: One-Click PowerShell Setup (Recommended)

Run the automated orchestrator from the project root:

```powershell
# Setup environment and start all services
.\setup_system.ps1

# Alternative modes:
.\setup_system.ps1 -SetupOnly    # Only install Python & Node dependencies
.\setup_system.ps1 -RunOnly      # Skip setup and start servers
```

---

### Option 2: Manual Step-by-Step Setup

#### 1. Setup Python Environment & Backend
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.common.txt

# (Optional) Retrain ML models if needed
python train_models.py
python train_salary_model.py

# Start Flask Backend API (Port 5000)
python app.py
```

#### 2. Setup React Frontend
```powershell
cd "UI Eduplus"

# Install Node modules
npm install

# Start Vite dev server (Port 5173)
npm run dev
```

#### 3. Setup Rasa Chatbot (Optional for Chatbot features)
```powershell
cd Chatbot

# Train Rasa NLU model
rasa train

# Run Rasa Action Server (Port 5055)
rasa run actions

# In a separate terminal, run Rasa Webhook Server (Port 5005)
rasa run --enable-api --cors "*"
```

---

## 🌐 Service Ports Summary

| Service | Port | Description |
| :--- | :--- | :--- |
| **Flask API** | `http://localhost:5000` | Main backend API endpoint |
| **React Frontend** | `http://localhost:5173` | Interactive student web dashboard |
| **Rasa Webhook** | `http://localhost:5005` | Rasa NLP chatbot service |
| **Rasa Actions** | `http://localhost:5055` | Custom database query handler for Rasa |
| **Isolated LLM** | `http://localhost:8001` | EduNavigator RAG server |

---

## 📑 Core Documentation Index

Additional detailed technical documentation is available in the repository root:
- [`SETUP_AND_STARTUP_GUIDE.md`](file:///d:/Work/SY%20Work/Sem%201/Eduplus/Eduplus%20Integation/plcement%20integrted%20-%20Copy%20%282%29/SETUP_AND_STARTUP_GUIDE.md) — Comprehensive environment setup details.
- [`INFO.md`](file:///d:/Work/SY%20Work/Sem%201/Eduplus/Eduplus%20Integation/plcement%20integrted%20-%20Copy%20%282%29/INFO.md) — Deep-dive system architecture and API documentation.
- [`QUICK_REFERENCE.md`](file:///d:/Work/SY%20Work/Sem%201/Eduplus/Eduplus%20Integation/plcement%20integrted%20-%20Copy%20%282%29/QUICK_REFERENCE.md) — Quick command reference for commands and APIs.
- [`VISUAL_SUMMARY.md`](file:///d:/Work/SY%20Work/Sem%201/Eduplus/Eduplus%20Integation/plcement%20integrted%20-%20Copy%20%282%29/VISUAL_SUMMARY.md) — Visual workflow diagrams and user journeys.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
