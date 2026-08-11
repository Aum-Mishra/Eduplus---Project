# Eduplus Campus Placement System - Setup & Startup Guide

## 📋 Complete Step-by-Step Guide

**Time to Complete:** 45-60 minutes
**Difficulty:** Beginner-friendly

---

## Phase 1: Prerequisites Check (5 minutes)

### Step 1.1: Verify Windows Version
```powershell
# Check Windows version
winver

# Should be: Windows 10 or later
```

### Step 1.2: Verify Python 3.10
```powershell
# Check if Python 3.10 is installed
py -3.10 --version

# Should show: Python 3.10.x (like 3.10.12)
```

**If not installed:**
1. Download Python 3.10 from https://www.python.org/downloads/
2. Install with checkmark on "Add Python to PATH"
3. Verify again with `py -3.10 --version`

### Step 1.3: Verify Node.js
```powershell
# Check Node.js version
node --version
npm --version

# Should show: v16+ and npm 8+
```

**If not installed:**
1. Download Node.js LTS from https://nodejs.org/
2. Install (includes npm)
3. Verify with commands above
4. Restart PowerShell after installation

### Step 1.4: Verify Git (Optional)
```powershell
git --version

# Not required, but helpful for version control
```

---

## Phase 2: Download & Navigate (2 minutes)

### Step 2.1: Open PowerShell
```powershell
# Right-click desktop and select "Open PowerShell here"
# OR search for "PowerShell" in Start menu
```

### Step 2.2: Navigate to Project
```powershell
# Navigate to project directory
cd "d:\Work\SY Work\Sem 1\Eduplus\Eduplus Integation\plcement integrted - Copy (2)"

# Verify you're in the right place
ls README.md
# Should show the README file
```

### Step 2.3: Verify Project Files
```powershell
# Check that main files exist
ls app.py
ls requirements.txt
ls setup_all.ps1
ls start_all.ps1
ls stop_all.ps1
ls check_services.ps1
ls UI Eduplus
ls Chatbot
ls data
ls models

# All should exist
```

---

## Phase 3: One-Time System Setup (30-40 minutes)

### Step 3.1: Run Setup Script
```powershell
# Execute setup (creates isolated venvs, installs deps, trains models)
.\setup_all.ps1

# This will:
# ✓ Validate prerequisites
# ✓ Create .venv_backend, .venv_rasa, and .venv_rag
# ✓ Install split Python packages for each service
# ✓ Install frontend packages (React, Vite, TailwindCSS)
# ✓ Train all 5 ML models
# ✓ Train Rasa chatbot model if missing
```

**This process takes 30-40 minutes. Grab coffee ☕!**

### Step 3.2: Wait for Completion
You should see:
```
==== EDUPLUS SETUP COMPLETE ====
```

### Step 3.3: Verify Setup Completed
```powershell
# Check virtual environments created
ls .venv_backend
ls .venv_rasa
ls .venv_rag

# Check ML models trained
ls models\placement_model.pkl
ls models\salary_model.pkl
ls models\job_role_model.pkl
ls models\company_knn_model.pkl
ls models\salary_tier_model.pkl

# Check Rasa model trained
ls Chatbot\models\current.tar.gz

# Check frontend packages installed
ls UI Eduplus\node_modules
```

All files should exist. If any missing, troubleshoot (see end of guide).

---

## Phase 4: Starting All Services (5 minutes)

### Step 4.1: Launch All Services
```powershell
# Start all 5 services in separate terminals
.\start_all.ps1

# This opens 5 new terminal windows:
# 1. Flask API (:5000)
# 2. Rasa HTTP Server (:5005)
# 3. Rasa Action Server (:5055)
# 4. RAG Service (:8001)
# 5. Frontend (Vite) (:5173)
```

### Step 4.2: Wait for Services to Start
Each terminal shows startup messages. Wait ~30-60 seconds for all to be ready.

**Terminal 1 - Flask Backend (port 5000):**
```
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5000
```

**Terminal 2 - Rasa Action Server (port 5055):**
```
[INFO] Starting Rasa action server... 
Action server is up and running.
```

**Terminal 3 - Rasa HTTP Server (port 5005):**
```
[INFO] Started Rasa server at http://0.0.0.0:5005
```

**Terminal 4 - LLM Service (port 8001):**
```
 * Running on http://0.0.0.0:8001
```

**Terminal 5 - Frontend (usually port 5173):**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  press h + enter to show help
```

### Step 4.3: Verify Services Running
```powershell
# In a new PowerShell window, test each service:

# Test Flask API
curl http://localhost:5000/health

# Test Rasa API
curl http://localhost:5005/

# Test LLM Service
curl http://localhost:8001/health

# Test Frontend (should return HTML)
curl http://localhost:5173
```

All should respond without errors.

---

## Phase 5: Access the System (5 minutes)

### Step 5.1: Open Dashboard
```powershell
# Option 1: Click link from Vite terminal
# Option 2: Manually open browser
# URL: http://localhost:5173
```

**You should see:**
- Eduplus logo
- Student dashboard
- Prediction results
- Company listings
- Navigation menu

### Step 5.2: Test Predictions
1. Go to "Predictions" page
2. Enter student details:
   - CGPA: 8.5
   - Skills: Python, Java
   - Internships: 1
   - Projects: 3
3. Click "Generate Predictions"
4. View results from all 5 models

### Step 5.3: Test Chatbot
1. Go to "Chat" page
2. Type: "What's my placement probability?"
3. Chat responds with prediction

### Step 5.4: View Companies
1. Go to "Companies" page
2. Browse company database
3. Filter by difficulty or skills

---

## Phase 6: Understanding the Services

### What Each Service Does

#### Flask Backend (Terminal 1)
```
Purpose: Serve ML model predictions
Port: 5000
Endpoints:
  - /api/predictions/generate
  - /api/predictions/placement
  - /api/predictions/salary
  - /api/recommendations/companies
  - etc.
```

**Keep this running** - Core predictions depend on it

#### Rasa Chatbot (Terminals 2 & 3)
```
Purpose: Conversational AI for career guidance
Ports: 5055 (Actions), 5005 (HTTP)
Handles:
  - User questions
  - Intent recognition
  - Entity extraction
  - Multi-turn conversations
```

**Keep these running** - Chat features depend on them

#### LLM Service (Terminal 4)
```
Purpose: Additional text generation
Port: 8001
Used for:
  - Summary generation
  - Report writing
  - Career guidance suggestions
```

**Keep this running** - Some features depend on it

#### Frontend (Terminal 5)
```
Purpose: Interactive dashboard
Port: 5173
Features:
  - Real-time updates
  - Interactive charts
  - Form inputs
  - Responsive design
```

**Keep this running** - This is how users interact with system

---

## Phase 7: Common Tasks

### View ML Model Predictions Directly

#### Via API (using curl)
```powershell
# Create a JSON file with student data
$body = @{
    cgpa = 8.5
    skills = @("Python", "Java", "SQL")
    internships = 1
    projects = 3
    certifications = @("AWS")
    branch = "CSE"
    batch = 2024
} | ConvertTo-Json

# Make prediction request
curl -X POST http://localhost:5000/api/predictions/generate `
  -ContentType "application/json" `
  -Body $body

# Response shows all 5 model predictions
```

#### Via Dashboard
1. Go to http://localhost:5173
2. Click "Predictions"
3. Fill in student details
4. See visualized results

### View API Documentation

#### Flask Endpoints
```
Most Flask endpoints available at:
http://localhost:5000/

Check app.py for all endpoints
```

#### Rasa Intents
```
View trained intents:
- Chatbot/domain.yml
- Chatbot/data/nlu.yml
- Chatbot/data/stories.yml
```

### Train Models Again
```powershell
# If you update data and want to retrain:

# Activate virtual environment
.\.venv_all\Scripts\Activate.ps1

# Train all models
python train_models.py

# Or specific model
python train_salary_model.py

# Retrain Rasa
cd Chatbot
python -m rasa train
```

### Test System Components
```powershell
# Validate entire system
python validate_system.py

# Generate model evaluation report
python evaluate_ml_models_report.py

# Creates: reports/model_evaluation/
```

---

## Phase 8: Stopping Services

### Stop All Services
```powershell
# Option 1: Close each terminal manually
# In each terminal window, press: Ctrl+C

# Option 2: Batch close via PowerShell
# Run this in a new terminal:
Get-Process python | Stop-Process -Force
Get-Process node | Stop-Process -Force
```

### Graceful Shutdown
```powershell
# For each terminal:
# Press: Ctrl+C

# Wait for "Shutdown complete" message
# Then close the window
```

**Do NOT forcefully close terminals** - Let services shutdown gracefully

---

## Phase 9: Troubleshooting

### Problem: "Python 3.10 not found"
**Solution:**
```powershell
# Check available Python versions
py -0

# If 3.10 not shown:
1. Download Python 3.10 from python.org
2. Install with "Add to PATH" checkbox
3. Restart PowerShell
4. Try again: py -3.10 --version
```

### Problem: "Port 5000 already in use"
**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change Flask port in app.py
# Change: app.run(port=5000)
# To: app.run(port=5001)
```

### Problem: "Setup script won't run"
**Solution:**
```powershell
# Check execution policy
Get-ExecutionPolicy

# If restricted, allow:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try again
.\setup_system.ps1 -SetupOnly
```

### Problem: "npm packages won't install"
**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -Recurse "UI Eduplus\node_modules"

# Reinstall
cd "UI Eduplus"
npm install
```

### Problem: "ML models not found after setup"
**Solution:**
```powershell
# Manually train models
.\.venv_all\Scripts\Activate.ps1
python train_models.py

# Wait for completion
# Check: ls models\*.pkl
```

### Problem: "Rasa model training failed"
**Solution:**
```powershell
# Delete old model
rm Chatbot\models\current.tar.gz

# Retrain
.\.venv_all\Scripts\Activate.ps1
cd Chatbot
python -m rasa train

# Verify: ls models\current.tar.gz
```

### Problem: "Frontend won't load at localhost:5173"
**Solution:**
```powershell
# Check Vite terminal for errors
# Common fixes:

# 1. Reinstall dependencies
cd "UI Eduplus"
npm install

# 2. Clear cache
rm -Recurse .next
npm cache clean --force

# 3. Try different port
npm run dev -- --port 3000
# Then access: http://localhost:3000
```

### Problem: "Chatbot returns empty responses"
**Solution:**
```powershell
# Check Rasa is running
curl http://localhost:5005/

# Check action server is running  
curl http://localhost:5055/

# Restart both:
# 1. Close both Rasa terminals
# 2. Run setup_system.ps1 -RunOnly again
```

---

## Phase 10: Performance Tips

### Speed Up Setup (Next Time)
```powershell
# Skip some training steps if models already exist
# Edit setup_system.ps1 before running

# Or just run:
.\setup_system.ps1 -RunOnly
# (Skips training, assumes models exist)
```

### Faster ML Predictions
```powershell
# Models load on first request
# Subsequent requests are faster
# 
# First request: ~2-3 seconds
# Cached requests: <100ms
```

### Reduce Memory Usage
```powershell
# Only run services you need
# Comment out in setup_system.ps1:
# 
# # Don't need Rasa? Comment these:
# # Start-Process cmd ... Rasa ...
#
# # Don't need LLM? Comment:
# # Start-Process cmd ... llm ...
```

### Use GPU for Faster Inference
```
Model training can use GPU if available
Current setup uses CPU (slower but compatible)

To enable GPU:
1. Install CUDA 11.x
2. Install cuDNN
3. Install tensorflow-gpu or torch
4. Update requirements.txt

Not recommended unless models very large
```

---

## Phase 11: Running Services Individually

### Start Only Flask Backend
```powershell
.\.venv_all\Scripts\Activate.ps1
python app.py

# Accessible at: http://localhost:5000
```

### Start Only Frontend
```powershell
cd "UI Eduplus"
npm run dev

# Accessible at: http://localhost:5173
```

### Start Only Chatbot
```powershell
.\.venv_all\Scripts\Activate.ps1

# Terminal 1:
cd Chatbot
python -m rasa run actions --enable-api --port 5055

# Terminal 2:
cd Chatbot
python -m rasa run --enable-api --port 5005
```

### Start Only LLM Service
```powershell
.\.venv_all\Scripts\Activate.ps1
cd llm_isolated_service
python app.py

# Accessible at: http://localhost:8001
```

---

## Phase 12: Production Deployment

### For Server Deployment
```
1. Install Python 3.10 on server
2. Install Node.js on server
3. Copy project files
4. Run: .\setup_system.ps1 -SetupOnly
5. Use production WSGI server:
   - Gunicorn (Linux)
   - CherryPy (Windows)
   - uWSGI
6. Use production frontend build:
   npm run build
   # Serves dist/ folder
7. Use systemd/services for auto-restart
```

### For Docker Deployment
```
1. Create Dockerfile
2. Build image: docker build -t eduplus .
3. Run container: docker run -p 5000:5000 ...
4. Expose all 5 ports
```

### For Cloud Deployment
```
1. AWS EC2 / Azure VM / GCP Compute
2. Same setup as server
3. Use cloud managed databases
4. Scale models with load balancer
5. Use CDN for frontend
```

---

## Phase 13: Daily Operations

### Check System Health
```powershell
# Test all services
curl http://localhost:5000/health
curl http://localhost:5005/
curl http://localhost:5055/
curl http://localhost:8001/health
curl http://localhost:5173

# All should respond without errors
```

### View Recent Predictions
```
1. Go to Dashboard: http://localhost:5173
2. See "Recent Activity"
3. Click on any student for details
```

### Check Model Performance
```powershell
# Generate evaluation report
.\.venv_all\Scripts\Activate.ps1
python evaluate_ml_models_report.py

# Check: reports/model_evaluation/
```

### Update Student Data
```powershell
# Add new students
.\.venv_all\Scripts\Activate.ps1
python update_profiles.py

# Update placement data
# Edit: data/student_profiles_100.csv
# Then restart Flask for changes to take effect
```

---

## Quick Reference

### Startup Command
```powershell
# Full setup (first time)
.\setup_system.ps1 -SetupOnly

# Start services (every time)
.\setup_system.ps1 -RunOnly
```

### Service Ports
```
Frontend:           http://localhost:5173
Flask API:          http://localhost:5000
Rasa HTTP:          http://localhost:5005
Rasa Actions:       http://localhost:5055
LLM Service:        http://localhost:8001
```

### Key Files
```
Main API:           app.py
Chatbot:            Chatbot/
Frontend:           UI Eduplus/
ML Models:          models/
Data:               data/
Setup Script:       setup_system.ps1
```

### Training Commands
```powershell
# ML Models
python train_models.py
python train_salary_model.py

# Chatbot
cd Chatbot && python -m rasa train

# Evaluate
python evaluate_ml_models_report.py
```

---

## Support & Help

### Verify Setup Worked
Run this test:
```powershell
python validate_system.py

# Should show: ✓ All systems functional
```

### Read Documentation
- **PROJECT_COMPLETE_GUIDE.md** - Architecture & components
- **PROJECT_SUMMARY.md** - Quick overview
- **app.py** - API endpoints (code comments)
- **modules/ml_models.py** - ML model details

### Check Logs
Each terminal shows live output:
- Flask terminal: API request logs
- Rasa terminals: Intent/entity recognition
- Frontend terminal: Build/compilation messages
- LLM terminal: Generation requests

---

## Success Checklist

- [ ] Python 3.10 verified
- [ ] Node.js verified
- [ ] Project downloaded/accessed
- [ ] Setup completed successfully
- [ ] All 5 ML models trained
- [ ] Rasa model trained
- [ ] Frontend dependencies installed
- [ ] All services started
- [ ] Flask API responding
- [ ] Rasa chatbot working
- [ ] Frontend loads at :5173
- [ ] Can make predictions
- [ ] Can chat with bot
- [ ] Can view companies
- [ ] Dashboard displays data

---

## You're Ready!

✅ System is running
✅ Services are operational
✅ Ready for use

### Next Steps
1. Explore dashboard: http://localhost:5173
2. Test predictions with student data
3. Chat with the chatbot
4. View company listings
5. Generate reports

---

**Created:** August 2025
**Version:** 1.0
**Estimated Setup Time:** 45-60 minutes (first time)
**Estimated Setup Time:** <5 minutes (subsequent times)

🎉 **Enjoy using Eduplus Campus Placement System!**
