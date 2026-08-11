# Eduplus Quick Reference Guide

**Bookmark this page for quick commands and information!**

---

## 🚀 Quick Start (30 seconds)

```powershell
# First time only (45 minutes)
.\setup_all.ps1

# Every time you want to use the system (5 seconds)
.\start_all.ps1

# Then open browser
http://localhost:5173
```

---

## 📍 Service Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Frontend** | 5173 | http://localhost:5173 | Dashboard, UI |
| **Flask API** | 5000 | http://localhost:5000 | ML predictions |
| **Rasa HTTP** | 5005 | http://localhost:5005 | Chatbot API |
| **Rasa Actions** | 5055 | http://localhost:5055 | Custom actions |
| **RAG Service** | 8001 | http://localhost:8001 | FastAPI + LangChain + FAISS |

---

## 🎯 What Each Service Does

```
Frontend (:5173)
├─ Student Dashboard
├─ Prediction Results
├─ Company Listings
├─ Chat Interface
└─ Reports & Analytics

Flask API (:5000)
├─ Placement Probability
├─ Salary Prediction
├─ Job Role Suggestion
├─ Company Recommendations
└─ Salary Tier Classification

Chatbot (:5005 + :5055)
├─ Answer questions
├─ Provide guidance
├─ Query database
└─ Multi-turn conversations

LLM Service (:8001)
├─ Text generation
├─ Summarization
└─ Career advice writing
```

---

## 🏗️ Project Structure

```
Root/
├─ app.py                    Main Flask backend
├─ Chatbot/                  Rasa chatbot
├─ UI Eduplus/               React frontend
├─ data/                     CSV datasets
├─ models/                   Trained .pkl files
├─ modules/                  Python helper modules
├─ llm_isolated_service/     Text generation service
├─ setup_all.ps1             Setup script
├─ start_all.ps1             Start script
├─ stop_all.ps1              Stop script
└─ check_services.ps1        Health checks
```

---

## 🤖 The 5 ML Models

| # | Model | Purpose | Output |
|---|-------|---------|--------|
| 1 | **Placement Probability** | Will student get placed? | 0.85 (85% chance) |
| 2 | **Salary Prediction** | How much will they earn? | 8.5 LPA |
| 3 | **Job Role** | What role suits them? | Software Developer |
| 4 | **Company Recommendations** | Which companies to apply? | Top 5 matches |
| 5 | **Salary Tier** | Which salary bracket? | Tier 3 (8-12 LPA) |

---

## 📊 Data Files

```
data/
├─ campus_placement_dataset_final_academic_4000.csv
│  (4000 historical student placement records)
│
├─ company_profiles_with_difficulty.csv
│  (Company database with difficulty ratings 1-10)
│
└─ student_profiles_100.csv
   (Current student data)
```

---

## 🎓 API Quick Reference

### Get All Predictions
```bash
POST http://localhost:5000/api/predictions/generate
Body: {cgpa: 8.5, skills: ["Python"], ...}
Returns: All 5 model predictions
```

### Get Placement Probability Only
```bash
POST http://localhost:5000/api/predictions/placement
Returns: Probability 0-1
```

### Get Company Recommendations
```bash
POST http://localhost:5000/api/recommendations/companies
Returns: Top 5 companies with match scores
```

### Chat with Bot
```bash
POST http://localhost:5005/webhooks/rest/webhook
Body: {"message": "Will I get placed?"}
Returns: Chatbot response
```

---

## 🔧 Common Commands

### Train Models
```powershell
# Activate environment
.\.venv_all\Scripts\Activate.ps1

# Train all
python train_models.py

# Train salary only
python train_salary_model.py

# Train chatbot
cd Chatbot
python -m rasa train
```

### Test System
```powershell
python validate_system.py        # Quick validation
python evaluate_ml_models_report.py  # Detailed report
```

### Update Data
```powershell
python update_profiles.py        # Update student/company data
```

### Stop Services
```
In each terminal: Ctrl+C
Wait for "Shutdown complete"
Then close window
```

---

## 🐛 Quick Troubleshooting

| Problem | Fix |
|---------|-----|
| **Port already in use** | `netstat -ano \| findstr :5000` then `taskkill /PID <id> /F` |
| **Python 3.10 not found** | Download from python.org, add to PATH |
| **npm install fails** | `npm cache clean --force`, try again |
| **Models not found** | Run `python train_models.py` |
| **Rasa fails** | Delete `Chatbot\models\`, retrain |
| **Frontend won't load** | Check Vite terminal, reinstall `UI Eduplus\node_modules` |

---

## ✅ Verification Commands

```powershell
# Test Flask API
curl http://localhost:5000/health

# Test Rasa
curl http://localhost:5005/

# Test LLM Service
curl http://localhost:8001/health

# Test Frontend
curl http://localhost:5173

# Comprehensive test
python validate_system.py
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **PROJECT_COMPLETE_GUIDE.md** | Full project explanation |
| **SETUP_AND_STARTUP_GUIDE.md** | Step-by-step setup |
| **This File** | Quick reference |
| **app.py** | API endpoints (code comments) |
| **PROJECT_SUMMARY.md** | Quick overview |

---

## 🎯 Typical Workflow

```
1. Start system
   .\setup_system.ps1 -RunOnly

2. Open browser
   http://localhost:5173

3. Enter student data
   CGPA, skills, internships, etc.

4. Click "Generate Predictions"
   See all 5 model results

5. Review recommendations
   Companies, salary, job role

6. Chat with bot (optional)
   Ask questions, get guidance

7. Export report (optional)
   Save as PDF

8. Stop services
   Ctrl+C in each terminal
```

---

## 💾 File Locations

```
Models:         models/*.pkl
Data:           data/*.csv
Frontend:       UI Eduplus/
Chatbot:        Chatbot/
API Code:       app.py
Backend:        modules/
Setup:          setup_system.ps1
```

---

## 🌟 Key Features at a Glance

```
✅ 5 Independent ML Models
✅ REST API for all predictions
✅ Conversational AI chatbot
✅ Real-time dashboard
✅ Company database with ratings
✅ Student profile tracking
✅ Placement history analysis
✅ Salary benchmarking
✅ Performance reports
✅ Easy to extend
```

---

## 📱 Dashboard Features

```
Home Tab
├─ Student profile summary
├─ Recent predictions
└─ Quick stats

Predictions Tab
├─ Input student data
├─ View all 5 model results
└─ Download report

Companies Tab
├─ Browse company database
├─ Filter by difficulty
└─ View placement stats

Chat Tab
├─ Talk to AI chatbot
├─ Get career advice
└─ Quick Q&A

Reports Tab
├─ Placement trends
├─ Salary analysis
└─ Comparative statistics
```

---

## 🔌 Integration Points

```
Flask (:5000)
    ├─ Loads ML models on startup
    ├─ Serves prediction requests
    ├─ Manages student data
    └─ Handles API requests

Chatbot (:5005, :5055)
    ├─ Recognizes user intent
    ├─ Calls Flask APIs
    ├─ Returns conversational response
    └─ Maintains conversation history

Frontend (:5173)
    ├─ Sends requests to Flask
    ├─ Sends messages to Chatbot
    ├─ Displays results
    └─ Updates visualizations

LLM Service (:8001)
    ├─ Generates text
    ├─ Summarizes results
    └─ Writes reports
```

---

## 🎓 Machine Learning Details

### Model Types
```
Placement Probability    → Classification (Binary)
Salary Value            → Regression
Job Role                → Classification (Multiclass)
Company Recommendations → K-Nearest Neighbors
Salary Tier             → Classification (Multiclass)
```

### Training Data
```
- 4000 historical records
- Features: CGPA, skills, internships, projects
- Labels: Placement status, salary, role, company
```

### Accuracy Metrics
```
Check: reports/model_evaluation/
Generated by: python evaluate_ml_models_report.py
```

---

## 🚀 Performance Expectations

| Operation | Time |
|-----------|------|
| Setup (first time) | 45 minutes |
| Service startup | 30 seconds |
| Model training | 5 minutes |
| Single prediction | <500ms |
| Batch predictions | 2-5 seconds |
| Chatbot response | 1-2 seconds |

---

## 💻 System Requirements

```
Minimum:
- Windows 10+
- Python 3.10+
- Node.js 16+
- 8 GB RAM
- 5 GB storage

Recommended:
- Windows 11
- Python 3.10.x
- Node.js 18+
- 16 GB RAM
- 10 GB storage
```

---

## 🔐 Security Notes

```
⚠️ Development only (not production)
⚠️ All services on localhost
⚠️ No authentication implemented
⚠️ CSV-based storage (not database)

For production:
→ Use proper database
→ Add authentication
→ Implement HTTPS
→ Add rate limiting
→ Use WSGI server
→ Add logging
→ Implement backups
```

---

## 📞 Quick Checklist

Before starting:
- [ ] Python 3.10 installed
- [ ] Node.js installed
- [ ] Project downloaded
- [ ] .venv_all exists
- [ ] Models exist in models/
- [ ] Rasa model trained

After starting:
- [ ] Flask running (:5000)
- [ ] Rasa running (:5005, :5055)
- [ ] Frontend running (:5173)
- [ ] LLM running (:8001)
- [ ] Dashboard loads
- [ ] Predictions work

---

## 🎯 One-Liner Commands

```powershell
# Full setup + start
.\setup_system.ps1 -SetupOnly; .\setup_system.ps1 -RunOnly

# Just start (next time)
.\setup_system.ps1 -RunOnly

# Only setup
.\setup_system.ps1 -SetupOnly

# Only run
.\setup_system.ps1 -RunOnly

# Test everything
python validate_system.py

# Generate reports
python evaluate_ml_models_report.py

# Train models
.\.venv_all\Scripts\Activate.ps1; python train_models.py
```

---

## 📖 Learn More

For detailed information, see:
1. **PROJECT_COMPLETE_GUIDE.md** - Full architecture
2. **SETUP_AND_STARTUP_GUIDE.md** - Step-by-step
3. **app.py** - API implementation
4. **modules/ml_models.py** - ML details
5. **Chatbot/domain.yml** - Intent definitions

---

## 🎉 Ready to Go!

```
✅ Quick reference created
✅ Commands at your fingertips  
✅ Services documented
✅ Troubleshooting available

Start now:
.\setup_system.ps1 -RunOnly
→ http://localhost:5173
```

---

**Last Updated:** August 2025
**Version:** 1.0
**Keep This Bookmarked!** 📌
