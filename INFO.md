# EduPlus System Information (Detailed)

## 1) What This Program Does
EduPlus is a multi-module placement intelligence platform for students. It combines:
- Profile-based placement prediction (probability, salary, role, company suggestions)
- Company intelligence (eligibility, package, rounds, skills, roadmap)
- LeetCode company question analytics and PDF reporting
- HR/aptitude/ATS and communication support
- Rasa chatbot + isolated LLM chatbot support
- Frontend portal for student login, prediction, and report export

The goal is to give each student data-backed placement guidance instead of generic advice.

## 2) High-Level Architecture
The project includes five major layers:

### A. Main Backend (Flask)
- File: app.py
- Runs APIs used by the React frontend and integrated chatbot flows
- Handles prediction generation, save/retrieve prediction records, integrations, and report logic

### B. ML Layer
- Files: modules/feature_engineering.py, modules/ml_models.py, modules/salary_probability.py, related utilities
- Performs feature prep, model inference, salary threshold probability estimation, and role/company recommendation

### C. Chatbot Layer (Rasa)
- Folder: Chatbot/
- Handles intent-based conversational workflows over placement/company data
- Uses custom actions in Chatbot/actions/

### D. Isolated LLM Layer
- Folder: llm_isolated_service/
- Runs a separate conversational API backed by local LLM (Ollama flow)
- Supports chat history, humanized response generation, and PDF/report helpers

### E. Frontend Layer
- Folder: UI Eduplus/
- React + Vite user interface
- Student login, dashboard, probability workflow, prediction report view, PDF download

## 3) Core Functional Features

### 3.1 Student Validation and Session Context
- Student logs in with student ID flow
- System loads student profile from CSV data stores
- Session-scoped interaction supports prediction + chatbot experiences

### 3.2 Placement Probability Prediction
- Uses student profile dimensions like DSA, projects, aptitude, HR, ATS, and academics
- Produces:
  - Overall placement probability
  - Predicted salary (LPA) and salary range
  - Salary-threshold probabilities (>2, >5, >10, >15, >20, >25, >30, >35, >40)
  - Predicted role and recommended companies

### 3.3 Low-Probability Guidance Mode
- For low placement probability cases, report format pivots to action mode
- Shows:
  - Why probability is low
  - Practical changes to improve outcomes
  - Risk and impact sections
  - Structured next-step plan

### 3.4 Company Intelligence
- Company tier, package, min CGPA, allowed departments, required skills
- Backlog policy and role notes
- Interview round details and preparation topics by area
- Company comparisons and filtered lists by profile criteria

### 3.5 LeetCode Company Question Insights
- Reads company-wise question datasets
- Supports time windows and question filters (difficulty/top-N/frequency)
- Returns analytics and generates downloadable PDF reports

### 3.6 Chatbot Support
Two chatbot approaches are available:
- Rasa intent/rule/policy based flow for deterministic actions
- Isolated LLM chatbot service for contextual humanized responses

### 3.7 PDF Reporting
- Prediction report export from frontend
- Structured sections for salary, probability, guidance, and advanced cards
- Table layout, section rendering, and branding support

## 4) Data and Model Assets
Main data locations:
- data/student_profiles_100.csv
- data/Predicted_Data.csv
- data/company_profiles_with_difficulty.csv
- data/company_placement_db.csv
- data/campus_placement_dataset_final_academic_4000.csv

Model/data outputs:
- models/*.pkl and related serialized artifacts
- Chatbot/models/*.tar.gz for trained Rasa models

## 5) Runtime Services and Typical Ports
When fully running the stack:
- Main Flask backend: 5000
- Rasa HTTP server: 5005
- Rasa action server: 5055
- Isolated LLM Flask service: 8001
- Frontend (Vite dev): usually 5173

## 6) End-to-End Workflow (Student Perspective)
1. Student logs in
2. System validates profile and loads current data
3. Student requests placement prediction
4. Backend computes probability/salary/role/company outputs
5. UI displays structured prediction cards and guidance
6. Student may ask chatbot for explanation/company prep help
7. Student downloads PDF report
8. Student revisits “My Predictions” with persisted records

## 7) Setup and Operations
A unified setup launcher is provided:
- setup_system.ps1

Modes:
- Full setup + run: .\setup_system.ps1
- Setup only: .\setup_system.ps1 -SetupOnly
- Run only: .\setup_system.ps1 -RunOnly

Unified Python dependencies are in:
- requirements.common.txt

## 8) Frontend and Python Dependency Model
- Python packages are unified in requirements.common.txt
- Node dependencies remain managed via UI Eduplus/package.json
- This split is intentional because frontend uses npm ecosystem while backend/chatbot/ML use Python ecosystem

## 9) Important Notes
- Recommended Python: 3.10.x (required by Rasa 3.6.x compatibility)
- Large binary/model/data artifacts can increase clone/push size
- Keep .gitignore aligned for virtual envs, transient build output, and cache files

## 10) Module Responsibility Summary
- app.py: primary API orchestration
- modules/: ML + scoring + feature engineering + service logic
- Chatbot/: Rasa NLU/dialog + custom actions
- llm_isolated_service/: local LLM API and advanced conversational layer
- UI Eduplus/: web client and report presentation

## 11) What Makes This Project Different
- Combines deterministic and generative conversational systems
- Uses data-backed prediction and company context together
- Supports both analytics and actionable student coaching
- Includes downloadable reports to operationalize guidance
