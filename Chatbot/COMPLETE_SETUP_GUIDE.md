# EduPlus PlaceMate AI - COMPLETE SETUP GUIDE

## ⚡ Quick Start (30 minutes)

### Prerequisites
- **Python 3.10** (REQUIRED - Rasa 3.6.13 requirement)
  - NOT 3.11, 3.12, 3.13, or earlier versions
  - Download: https://www.python.org/downloads/release/python-3100/

### Setup Steps

**1. Install Python 3.10**
- Download and install from python.org
- ✅ **IMPORTANT:** Check "Add Python 3.10 to PATH" during installation

**2. Open Command Prompt in the Chatbot folder**

**3. Run Setup (One Time)**
```cmd
setup_improved.bat
```
This script will:
- ✓ Verify Python version (3.10)
- ✓ Create virtual environment
- ✓ Install all dependencies (Rasa, pandas, etc.)
- ✓ Validate project structure
- ✓ Train the ML model (2-5 minutes)

**4. Start the Chatbot**
```cmd
run_improved.bat
```

**5. Test It**
```
> hi
> what is google's average package?
> how many tier 1 companies are there?
> goodbye
```

---

## 📊 Project Summary

| Component | Details |
|-----------|---------|
| **Framework** | Rasa 3.6.13 (NLU + Dialogue) |
| **Python** | 3.8, 3.9, or **3.10** (REQUIRED) |
| **Purpose** | College Placement ChatBot |
| **Companies** | 50 in knowledge base (CSV) |
| **Intents** | 24 different question types |
| **Custom Actions** | 40+ implemented |
| **Knowledge Source** | company_placement_db.csv |
| **Interfaces** | CLI (shell) + Web API |

---

## 🚨 CRITICAL: Python Version Issue Explained

**SYSTEM STATE:**
- Your system has: Python 3.13.1
- Rasa needs: Python 3.10 (or 3.8, 3.9)
- **Result:** Installation currently FAILS

**WHY THIS HAPPENS:**
- Rasa 3.6.13 was built and tested for Python 3.10 max
- Python 3.11+ changed internal APIs (breaking changes)
- Rasa dependencies (TensorFlow, etc.) don't support 3.13

**HOW TO FIX:**
→ Install Python 3.10 from python.org (5 minutes)
→ Run `setup_improved.bat`

---

## 📁 Project Structure

```
Chatbot/
│
├── 📄 SETUP_INSTRUCTIONS.md      ← Detailed setup guide
├── 📄 TROUBLESHOOTING.md          ← Fix common problems
├── 📄 validate_setup.py           ← Verify installation
│
├── setup_improved.bat             ← USE THIS (smart setup)
├── run_improved.bat               ← USE THIS (smart run)
│
├── setup.bat                      ← Original (basic version)
├── run.bat                        ← Original (basic version)
│
├── config.yml                     ← Rasa NLU config
├── domain.yml                     ← Intents & responses
├── credentials.yml                ← API credentials
├── endpoints.yml                  ← Server endpoints
├── requirements.txt               ← Dependencies
│
├── data/
│   ├── nlu.yml                   ← Intent training data (825 lines)
│   ├── stories.yml               ← Dialogue examples (59 lines)
│   ├── rules.yml                 ← Conversation rules (174 lines)
│   └── company_placement_db.csv   ← Knowledge base (50 companies)
│
├── actions/
│   ├── __init__.py
│   └── actions.py                ← Custom action handlers (916 lines)
│
├── ui/
│   └── index.html                ← Web interface (if server running)
│
├── models/                        ← Created after training
│   └── [TIMESTAMP].tar.gz        ← Trained ML model
│
└── venv_rasa/                     ← Created by setup (virtual env)
    └── Scripts/
        ├── activate.bat          ← Activate venv
        ├── python.exe            ← Python interpreter
        └── pip.exe               ← Package manager
```

---

## 🔧 Installation Options

### **Option A: Automated Setup (RECOMMENDED)**

**Best for:** Most users

```cmd
setup_improved.bat
```

Features:
- Auto-detects Python 3.10/3.9/3.8
- Creates isolated environment
- Installs all packages
- Trains model automatically
- **User-friendly** with clear messages

---

### **Option B: Manual Step-by-Step**

**Best for:** Learning or troubleshooting

```cmd
REM 1. Create virtual environment
python -m venv venv_rasa

REM 2. Activate it
venv_rasa\Scripts\activate.bat

REM 3. Upgrade pip
python -m pip install --upgrade pip setuptools wheel

REM 4. Install dependencies
pip install -r requirements.txt

REM 5. Verify Rasa installation
rasa --version

REM 6. Validate project
rasa data validate

REM 7. Train model (wait 2-5 min)
rasa train

REM 8. Run action server (Terminal 1)
rasa run actions

REM 9. Run chatbot shell (Terminal 2)
rasa shell
```

---

### **Option C: If Python 3.10 is named differently**

```cmd
REM Check what's available
python3.10 --version    # If exists
python3.9 --version     # If exists
python3.8 --version     # If exists

REM Use the compatible one
python3.10 -m venv venv_rasa    # Replace 3.10 with what you have
venv_rasa\Scripts\activate.bat
pip install -r requirements.txt
```

---

## ✅ Validation Steps

**After setup completes, run:**

```cmd
REM Test 1: Check Rasa version
rasa --version
REM Expected: rasa 3.6.13

REM Test 2: Validate project structure
rasa data validate
REM Expected: All checks pass

REM Test 3: Check model exists
dir models
REM Expected: See a .tar.gz file

REM Test 4: Start chatbot
REM Terminal 1:
rasa run actions
REM Expected: "Action server is running on 0.0.0.0:5055"

REM Terminal 2:
rasa shell
REM Expected: Chatbot prompt ">_"
```

---

## 🎮 Testing the Chatbot

Once `rasa shell` is running:

```
> hi
→ "Hi! I'm EduPlus PlaceMate AI..."

> what is Google's average package?
→ "Google Average Package: XX.X LPA"

> list tier-1 companies
→ "Tier-1 Companies: Google, Microsoft, Amazon..."

> what's the minimum CGPA for Amazon?
→ "Eligibility for Amazon: Min CGPA: X.X"

> am I eligible for Microsoft?
→ "Based on your profile: ..."

> goodbye
→ "Goodbye! Best of luck!"
```

---

## 📊 Dependency Details

### Required Packages
```
rasa 3.6.13           →  NLU + Dialogue Management
rasa-sdk 3.6.1        →  Custom Actions Framework
pandas 2.0.3          →  Data Processing (CSV)
fuzzywuzzy 0.18.0     →  Fuzzy String Matching
python-Levenshtein    →  String Distance Calculation
```

### Why These?
- **Rasa:** Main chatbot framework
- **rasa-sdk:** Allows custom Python actions for data queries
- **pandas:** Read company_placement_db.csv
- **fuzzywuzzy:** Handle user typos ("Microsoaft" → "Microsoft")
- **Levenshtein:** Implement string similarity algorithm

---

## 🏗️ Project Components Explained

### 1. **config.yml** - NLU Configuration
Defines how Rasa understands user intent:
- DIETClassifier: Latest intent/entity classifier
- RegexFeaturizer: Handles patterns like emails
- ResponseSelector: Picks best response from candidates
- FallbackClassifier: Handles unknown intents

### 2. **domain.yml** - Chatbot Vocabulary
Lists all valid intents, entities, and responses:
- 24 intents (ask_avg_package, ask_company_tier, etc.)
- 2 entities (company, prep_area)
- 5 slots (memory for context)
- 40+ predefined responses

### 3. **data/ Folder** - Training Data
- **nlu.yml (825 lines):** Examples of user queries by intent
- **stories.yml (59 lines):** Multi-turn conversation examples
- **rules.yml (174 lines):** Fixed rules (greeting always → greet response)
- **company_placement_db.csv:** 50 companies with data

### 4. **actions/actions.py** (916 lines)
Custom Python code that:
- Reads company_placement_db.csv
- Queries company data (packages, eligibility, etc.)
- Uses fuzzy matching for company name recognition
- Returns accurate, non-hallucinated responses

### 5. **ui/index.html**
Web interface for the chatbot (optional):
- Requires separate Node/Flask server to run
- Connects to Rasa API on port 5005

---

## 🔌 How It Works

```
User Input
    ↓
[Rasa NLU Pipeline]
    ↓
Intent Detection + Entity Extraction
    ↓
[Dialogue Manager (Policies)]
    ↓
Decide: Use Rule/Memory/TEDPolicy
    ↓
Select Action
    ↓
[Custom Action Handler]
    ↓
Query company_placement_db.csv → Fuzzy Matching
    ↓
Generate Response
    ↓
User sees response
```

---

## 🎯 Running Different Modes

### **Mode 1: Interactive Shell (Best for Testing)**
```cmd
rasa shell
```
Type naturally, get responses immediately

### **Mode 2: API Server (Best for Web/Mobile)**
```cmd
REM Terminal 1: Actions
rasa run actions

REM Terminal 2: API Server
rasa run -m models -p 5005 --enable-api --cors *
```

Then access at: `http://localhost:5005/webhooks/rest/webhook`

### **Mode 3: Web UI**
Requires Node.js server (see ui/README if exists):
```cmd
npm install
npm start
```

---

## ⚙️ Configuration Changes

### **To Lower Intent Confidence Threshold:**
Edit `config.yml`:
```yaml
- name: FallbackClassifier
  threshold: 0.5          # Was 0.6 → Accept lower confidence
  ambiguity_threshold: 0.1
```
Then retrain: `rasa train`

### **To Improve Response Speed:**
Edit `config.yml`, reduce epochs:
```yaml
- name: DIETClassifier
  epochs: 20              # Was 100 → Train faster
```

### **To Add New Company to Knowledge Base:**
1. Add row to `data/company_placement_db.csv`
2. No need to retrain (CSV is read at runtime)

### **To Add New Intent/Response:**
1. Add training examples to `data/nlu.yml`:
```yaml
- intent: new_intent
  examples: |
    - example 1
    - example 2
```
2. Add response to `domain.yml`:
```yaml
responses:
  utter_new_action:
    - text: "Response text"
```
3. Retrain: `rasa train`

---

## 🐛 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Python 3.13 error | Install Python 3.10, run setup_improved.bat |
| "No module named rasa" | `pip install rasa==3.6.13` |
| Connection refused | Ensure `rasa run actions` is running in Terminal 1 |
| Slow training | Normal: 2-5 min. If 10+ min, close other apps |
| Typos in company name | Fuzzy matching handles this automatically |
| CSV not found | Ensure `data/company_placement_db.csv` exists |

See **TROUBLESHOOTING.md** for detailed fixes.

---

## 📞 Support Files

- **SETUP_INSTRUCTIONS.md** → Detailed setup documentation
- **TROUBLESHOOTING.md** → Common problems & solutions
- **validate_setup.py** → Check your installation
- **setup_improved.bat** → Smart setup script
- **run_improved.bat** → Smart run script

Run validation anytime:
```cmd
python validate_setup.py
```

---

## 🎓 Learning Resources

- **Rasa Official:** https://rasa.com/docs/rasa
- **NLU Training:** https://rasa.com/docs/rasa/nlu-training-data
- **Custom Actions:** https://rasa.com/docs/rasa/custom-actions
- **Policies:** https://rasa.com/docs/rasa/policies
- **GitHub:** https://github.com/RasaHQ/rasa

---

## 📝 Checklist: Are You Ready?

Before running setup_improved.bat:

- [ ] Downloaded Python 3.10
- [ ] Installed Python 3.10 with "Add to PATH" checked
- [ ] You're in the Chatbot directory in Command Prompt
- [ ] `python --version` shows Python 3.10.x

After setup_improved.bat completes:

- [ ] No errors shown at the end
- [ ] "SUCCESS! Setup Complete" message displayed
- [ ] `models/` directory exists
- [ ] Can open two terminals

After starting chatbot:

- [ ] Terminal 1 shows: "action server is running"
- [ ] Terminal 2 shows: ">_" prompt
- [ ] Can type "hi" and get response
- [ ] Can ask about companies and get answers

---

## 🚀 Next Steps

**Immediate:**
1. ✓ Install Python 3.10
2. ✓ Run setup_improved.bat
3. ✓ Run run_improved.bat
4. ✓ Test with sample queries

**Short term (optional):**
- Add more training examples (improve accuracy)
- Expand company knowledge base
- Customize responses

**Long term (optional):**
- Deploy to cloud (Heroku, AWS, etc.)
- Connect to web/mobile frontend
- Integrate with Slack or Teams
- Improve NLP model

---

## 📞 Questions?

1. Check **SETUP_INSTRUCTIONS.md** for detailed info
2. Run `python validate_setup.py` for diagnostics
3. See **TROUBLESHOOTING.md** for common issues
4. Check Rasa docs: https://rasa.com/docs

---

**Project:** EduPlus PlaceMate AI
**Framework:** Rasa 3.6.13
**Date:** February 25, 2026
**Status:** Complete - Ready for Python 3.10 installation

