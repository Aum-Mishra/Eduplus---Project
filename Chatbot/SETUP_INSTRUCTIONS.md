# EduPlus PlaceMate AI - Complete Setup Guide

## ⚠️ Critical Issue: Python Version Compatibility

**Current System Status:**
- **Installed Python:** 3.13.1
- **Required Python:** 3.8, 3.9, or 3.10 (for Rasa 3.6.13)

### The Problem
Rasa 3.6.13 (specified in `requirements.txt`) was officially tested and built only for Python 3.8, 3.9, and 3.10. Python 3.13 introduces breaking changes that make Rasa 3.6.13 incompatible.

---

## 🔧 Solution Options

### **Option 1: Install Python 3.10 (RECOMMENDED)**

This is the easiest and most reliable solution.

#### Steps:
1. **Download Python 3.10**
   - Visit: https://www.python.org/downloads/release/python-3100/
   - Download: **Windows x86-64 executable installer**

2. **Install Python 3.10**
   - Run the installer
   - ✅ **CHECK THE BOX:** "Add Python 3.10 to PATH"
   - Choose "Install for all users" (optional)
   - Close the installer

3. **Verify Installation**
   ```cmd
   python3.10 --version
   ```
   Expected output: `Python 3.10.0`

4. **Run Setup Script**
   Open Command Prompt (CMD) in the Chatbot directory and run:
   ```cmd
   setup.bat
   ```

5. **Start the Chatbot**
   After setup completes successfully, run:
   ```cmd
   run.bat
   ```

---

### **Option 2: Use Virtual Environment with Python 3.10 (If Python 3.13 is still Python default)**

If you install Python 3.10 but Python 3.13 is still the default, use this approach:

```cmd
:: Create venv with Python 3.10
python3.10 -m venv venv_rasa

:: Activate venv
venv_rasa\Scripts\activate.bat

:: Install dependencies
pip install -r requirements.txt

:: Validate project
python -m rasa data validate

:: Train chatbot
python -m rasa train

:: Run chatbot
python -m rasa shell
```

---

### **Option 3: Use Conda (Advanced Users)**

If you have Conda installed:

```bash
conda create -n rasa-env python=3.10
conda activate rasa-env
pip install -r requirements.txt
rasa train
rasa shell
```

---

## 📋 Project Structure Analysis

```
Chatbot/
├── config.yml              # Rasa NLU and Dialogue policy config
├── domain.yml              # Intent, entity, and response definitions
├── credentials.yml         # API credentials (if needed)
├── endpoints.yml           # Action server and channel endpoints
├── requirements.txt        # Python dependencies
│
├── data/
│   ├── nlu.yml            # Intent training data (825 lines)
│   ├── stories.yml        # Dialogue stories (59 lines)
│   ├── rules.yml          # Conversation rules (174 lines)
│   └── company_placement_db.csv  # Knowledge base (50 companies)
│
├── actions/
│   ├── __init__.py
│   └── actions.py         # Custom action handlers (916 lines)
│
├── tests/
│   ├── test_stories.yml   # Test dialogue scenarios
│   └── verify_cleanup.py
│
├── ui/
│   └── index.html         # Web UI interface
│
├── setup.bat / setup.sh   # Automated setup scripts
└── run.bat / run.sh       # Automated run scripts
```

---

## 🎯 Project Specification

**Project Type:** Rasa 3.6.13 Chatbot
- **Purpose:** College Placement Assistance (EduPlus PlaceMate AI)
- **Model Version:** Rasa 3.6.13 (requires Python 3.8-3.10)
- **Interface:** Shell CLI + Web UI
- **Data Source:** CSV database (company_placement_db.csv)

---

## 📊 Dependency Analysis

### Core Dependencies (from requirements.txt)
```
rasa==3.6.13              # NLU & Dialogue management framework
rasa-sdk==3.6.1           # Rasa SDK for custom actions
pandas==2.0.3             # Data processing library
fuzzywuzzy==0.18.0        # Fuzzy string matching (company names)
python-Levenshtein==0.21.1  # String distance algorithm
```

### Key Components
- **NLU Pipeline:**
  - WhitespaceTokenizer, RegexFeaturizer
  - DIETClassifier (latest supervised learning)
  - EntitySynonymMapper, ResponseSelector
  - FallbackClassifier (confidence threshold: 0.6)

- **Dialogue Policies:**
  - RulePolicy (handles rule-based conversations)
  - MemoizationPolicy (remembers exact conversations)
  - TEDPolicy (learns complex patterns)

- **Custom Actions:**
  - ~40 custom action classes in `actions/actions.py`
  - Actions for:
    - Querying company data
    - Generating eligibility summaries
    - Providing preparation tips
    - Analytics queries

---

## ✅ Step-by-Step Manual Setup (Once Python 3.10 is installed)

### 1. Create Virtual Environment
```cmd
cd Chatbot
python -m venv venv_rasa
venv_rasa\Scripts\activate.bat
```

### 2. Install Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Validate Project Structure
```cmd
rasa data validate
```
Expected output: ✅ All validation checks pass

### 4. Train the Model
```cmd
rasa train
```
Expected output: Model saved to `models/`

### 5. Run Custom Actions Server (Terminal 1)
```cmd
python -m rasa run actions
```
Expected: "action server is running"

### 6. Run Rasa Shell (Terminal 2)
```cmd
rasa shell
```

### 7. Test the Chatbot
```
> hi
> what are Google's packages?
> list tier-1 companies
> goodbye
```

---

## 🏃 Quick Start (After Everything is Installed)

### Easiest: Use Provided Scripts

**Windows:**
```cmd
setup.bat    # Run once to install (requires Python 3.10)
run.bat      # Run multiple times to start
```

**Linux/Mac:**
```bash
chmod +x setup.sh run.sh
./setup.sh   # Run once
./run.sh     # Run multiple times
```

### Manual: Step by Step
```cmd
:: Terminal 1: Start action server
venv_rasa\Scripts\activate.bat
python -m rasa run actions

:: Terminal 2: Start chatbot
venv_rasa\Scripts\activate.bat
rasa shell
```

---

## 🧪 Validation Checklist

After setup, verify everything works:

- [ ] `python --version` shows 3.10.x or 3.9.x
- [ ] `pip list | findstr rasa` shows rasa 3.6.13
- [ ] `rasa --version` displays Rasa 3.6.13
- [ ] `rasa data validate` shows no errors
- [ ] `models/` directory exists with trained model
- [ ] `rasa shell` starts without errors
- [ ] Chatbot responds to greetings ("Hi" → greeting response)
- [ ] Chatbot queries companies ("What about Google?")
- [ ] Chatbot handles unknown queries gracefully

---

## 🐛 Troubleshooting

### Error: "Python version 3.8, 3.9, or 3.10 required"
**Fix:** Install Python 3.10 from python.org

### Error: "No module named rasa"
**Fix:** 
1. Ensure venv is activated: `venv_rasa\Scripts\activate.bat`
2. Reinstall: `pip install rasa==3.6.13`

### Error: "Models directory not found"
**Fix:** Train the model: `rasa train`

### Error: "Connection refused" when starting shell
**Fix:** Ensure action server is running in another terminal: `rasa run actions`

### Custom action errors
**Fix:** 
1. Check CSV exists: `data/company_placement_db.csv`
2. Verify Python can read it: `python -c "import pandas; pd.read_csv('data/company_placement_db.csv')"`

---

## 📝 Project Notes

### NLU Configuration
- **Language:** English
- **Tokenizer:** Whitespace-based
- **Entity Extraction:** Regex + DIET Classifier
- **Intent Classification:** DIETClassifier (100 epochs)

### Policies
- **Rule-based:** Handles fixed patterns (greetings, goodbyes)
- **Memorization:** Reminds exact training examples
- **TEDPolicy:** Learns complex patterns (max history: 5 turns)

### Data Knowledge Base
- **50 Companies** in CSV database
- **24 Intents** covering:
  - Basic (greet, goodbye, thank_you)
  - Company-specific (packages, eligibility, skills)
  - Aggregate queries (list by tier, CGPA)
  - Policy questions

### Custom Actions
- Company data lookup with fuzzy matching
- Eligibility checking based on CGPA and backlogs
- Preparation roadmap generation
- Analytics queries

---

## 🎓 Configuration Files Explained

### config.yml
Defines the NLU pipeline and dialogue policies. The DIETClassifier is the modern replacement for old intent/entity extractors.

### domain.yml
Maps all intents, entities, slots, and predefined responses. This is the chatbot's vocabulary.

### stories.yml / rules.yml
- **Stories:** Training examples of multi-turn conversations
- **Rules:** Fixed patterns that should always be followed

### credentials.yml / endpoints.yml
- **credentials.yml:** API keys and tokens (GitHub, Slack, etc.)
- **endpoints.yml:** Addresses of action server and channels

---

## 📚 Additional Resources

- **Rasa Blog:** https://blog.rasa.com
- **Rasa Docs:** https://rasa.com/docs
- **Training Data Format:** https://rasa.com/docs/rasa/nlu-training-data
- **Custom Actions:** https://rasa.com/docs/rasa/custom-actions

---

## 🚀 Next Steps After Setup

Once the chatbot is running:

1. **Test in Shell:** Talk to the chatbot interactively
2. **Test API:** Use the HTTP API at `http://localhost:5005`
3. **Integrate UI:** Open `ui/index.html` in browser (if Flask/Node server is set up)
4. **Extend:** Add new intents to `data/nlu.yml` and retrain
5. **Deploy:** Use Docker or cloud platforms (Rasa X, Heroku, AWS)

---

**Setup Date:** February 25, 2026
**Status:** Ready for Python 3.10 installation
**Last Updated:** Setup Guide v1.0
