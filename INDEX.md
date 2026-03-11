# � Placement AI System - Documentation Index

## 🎯 START HERE

**New to the system?** Start with these in order:

1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** ⭐ (5 min read)
   - What the system does
   - Quick setup (3 steps)
   - Two main scenarios
   - Common questions

2. **[FINAL_STATUS.md](FINAL_STATUS.md)** (10 min read)
   - What was fixed
   - System status
   - Feature checklist
   - How to run

3. **[WORKFLOW_UPDATED.md](WORKFLOW_UPDATED.md)** (20 min read)
   - Detailed workflow
   - Two-tier score management
   - Data flow diagram
   - CSV schema reference

---

## 📖 COMPLETE DOCUMENTATION

### Getting Started
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick start guide (5 min)
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Installation instructions
- [QUICKSTART.md](QUICKSTART.md) - First time setup

### Understanding the System
- [README.md](README.md) - Full system overview
- [WORKFLOW_UPDATED.md](WORKFLOW_UPDATED.md) - How it works
- [SYSTEM_FIXED_COMPLETE.md](SYSTEM_FIXED_COMPLETE.md) - Complete implementation
- [FINAL_STATUS.md](FINAL_STATUS.md) - System status & features

### Configuration & Reference
- [CONFIG_GUIDE.md](CONFIG_GUIDE.md) - Configuration options
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Technical summary

### Validation
- [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) - Feature checklist
- [SYSTEM_READY.txt](SYSTEM_READY.txt) - System readiness check

---

## 🚀 QUICK NAVIGATION

### I want to...

**Get started immediately** 
→ Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
→ Run `python main.py`

**Understand the workflow**
→ Read [WORKFLOW_UPDATED.md](WORKFLOW_UPDATED.md) (20 min)

**See what was fixed**
→ Read [FINAL_STATUS.md](FINAL_STATUS.md) (10 min)

**Install and setup**
→ Read [SETUP_GUIDE.md](SETUP_GUIDE.md)
→ Run `pip install -r requirements.txt`

**Validate my system**
→ Run `python validate_system.py`
→ Check [SYSTEM_READY.txt](SYSTEM_READY.txt)

**Learn about features**
→ Read [README.md](README.md)
→ Check [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md)

**Configure settings**
→ Read [CONFIG_GUIDE.md](CONFIG_GUIDE.md)

**See technical details**
→ Read [SYSTEM_FIXED_COMPLETE.md](SYSTEM_FIXED_COMPLETE.md)
→ Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## 📊 DOCUMENTATION STRUCTURE

```
Documentation/
├── Entry Point
│   ├── QUICK_REFERENCE.md              ⭐ START HERE
│   ├── FINAL_STATUS.md                 ⭐ System Status
│   └── START_HERE.txt                  Quick links
│
├── Getting Started
│   ├── SETUP_GUIDE.md                  Installation
│   └── QUICKSTART.md                   First run
│
├── Understanding the System
│   ├── README.md                       Overview
│   ├── WORKFLOW_UPDATED.md             Detailed workflow
│   └── SYSTEM_FIXED_COMPLETE.md        Complete guide
│
├── Configuration
│   ├── CONFIG_GUIDE.md                 Settings
│   └── PROJECT_SUMMARY.md              Technical summary
│
├── Reference
│   ├── COMPLETION_CHECKLIST.md         Feature list
│   ├── SYSTEM_READY.txt                Readiness
│   └── INDEX.md                        This file
```

---

## 🎯 WHAT THE SYSTEM DOES

**Placement Prediction with Auto-Fetch**

```
Student ID → Auto-load from CSV → Conditional score collection → 
ML Models → Predictions → Display results → Auto-save to CSV
```

---

## 📋 KEY FEATURES

✅ **Auto-Fetch** - Remembers your data
✅ **Smart Updates** - Only update skills, not academics  
✅ **Instant Predictions** - Get results immediately
✅ **Company Suggestions** - Top 10 recommendations
✅ **Salary Estimates** - Predicted package with range
✅ **Data Persistence** - Everything saved in CSV

---

## 🔄 MAIN WORKFLOW

### New Student
```
Enter ID → Create profile → Collect 7 academic scores → 
Collect 5 skill scores → Auto-predict → Save to CSV
```

### Returning Student
```
Enter ID → Load profile → Show academic (read-only) → 
Show skills → Ask update? → Auto-predict → Update CSV
```

---

## 📂 FILE OVERVIEW

### Core System Files
- `main.py` - Application entry point (REWRITTEN)
- `train_models.py` - Train ML models
- `validate_system.py` - Validate setup (NEW)

### Module Files (9 total)
- `modules/student_profile.py` - Data management (ENHANCED)
- `modules/leetcode_dsa.py` - DSA scoring
- `modules/github_project.py` - Project evaluation
- `modules/aptitude_ats.py` - Test scoring
- `modules/hr_round.py` - Interview scoring
- `modules/feature_engineering.py` - Feature prep
- `modules/ml_models.py` - Model management
- `modules/company_logic.py` - Company rules
- `modules/prediction.py` - Predictions

### Data Files
- `data/student_profiles.csv` - Student database (NEW SCHEMA)
- `data/placement_dataset_training.csv` - Training data
- `data/company_profiles_with_difficulty.csv` - Company data
- `data/campus_placement_dataset_final_academic_4000.csv` - Academic data

### Model Files
- `models/placement_model.pkl` - Placement classifier
- `models/salary_model.pkl` - Salary regressor
- `models/jobrole_model.pkl` - Role classifier
- `models/knn_companies.pkl` - Company recommender
- `models/scaler.pkl` - Feature scaler

---

## 🎓 SCORE TYPES EXPLAINED

### Academic Scores (Permanent)
Collected once, never change:
- CGPA
- OS Score
- DBMS Score
- CN Score
- OOP Score
- System Design Score
- CS Fundamentals Score
- Hackathon Wins

### Variable Scores (Can Update)
Can be re-evaluated:
- DSA Score (from LeetCode)
- Project Score (from GitHub)
- Aptitude Score (from test)
- HR Score (from interview)
- Resume ATS Score (from analysis)

---

## 🔍 PREDICTION OUTPUTS

When you use the system, you get:

1. **Placement Probability** (%)
   - 0-100% chance of placement
   - Example: 92.5%

2. **Expected Salary** (₹ LPA)
   - Annual package prediction
   - Min-max range
   - Example: ₹12.5 LPA

3. **Job Role** (String)
   - Type of job position
   - Example: "Software Engineer"

4. **Company Type Probability** (%)
   - Service: 55%
   - Product: 45%

5. **Top 10 Companies**
   - Ranked recommendations
   - Individual probabilities

---

## 🛠️ SYSTEM REQUIREMENTS

- **Python:** 3.7+
- **Storage:** ~500 MB
- **RAM:** 4 GB minimum
- **Internet:** Optional (APIs have fallbacks)

---

## 📦 INSTALLATION

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train models (first time only)
python train_models.py

# 3. Run system
python main.py
```

---

## ✅ VALIDATION

```bash
# Check if everything is setup correctly
python validate_system.py
```

Should show:
- ✅ All files present
- ✅ All modules found
- ✅ CSV schema correct
- ✅ Packages installed
- ✅ Models trained

---

## 🎯 TYPICAL USER JOURNEY

```
First Visit (New Student)
├─ pip install -r requirements.txt
├─ python train_models.py
├─ python main.py
├─ Enter Student ID
├─ Collect 7 academic scores
├─ Collect 5 skill scores
├─ Get predictions
└─ Data saved to CSV

Later (Returning Student)
├─ python main.py
├─ Enter same Student ID
├─ System loads profile automatically
├─ Shows academic scores
├─ Asks if you want to update skills
├─ Get updated predictions
└─ Data updated in CSV

Next Time (Just Want New Predictions)
├─ python main.py
├─ Enter Student ID
├─ Ask "Update skills?" → NO
├─ Use existing scores
├─ Get predictions
└─ Done
```

---

## 📞 HELP & SUPPORT

### Getting Started
1. Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
2. Run `python validate_system.py`
3. Run `python main.py`

### Troubleshooting
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Check error messages
3. See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) troubleshooting section

### Understanding Features
1. Read [README.md](README.md) for overview
2. Read [WORKFLOW_UPDATED.md](WORKFLOW_UPDATED.md) for details
3. Check [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) for features

### Configuration
1. Read [CONFIG_GUIDE.md](CONFIG_GUIDE.md)
2. Modify settings as needed
3. Run `python main.py`

---

## 🌟 WHAT'S NEW (This Session)

- ✅ Rewrote main.py with auto-fetch workflow
- ✅ Enhanced student_profile.py with new CSV schema
- ✅ Updated CSV headers (19 columns)
- ✅ Added QUICK_REFERENCE.md
- ✅ Added WORKFLOW_UPDATED.md
- ✅ Added SYSTEM_FIXED_COMPLETE.md
- ✅ Added FINAL_STATUS.md
- ✅ Created validate_system.py
- ✅ Updated this INDEX.md

---

## 🎉 SYSTEM STATUS

**Status:** ✅ COMPLETE
**Version:** 2.0
**Last Updated:** This session
**Ready to Use:** YES

---

## 🚀 NEXT STEPS

1. **Start Here:** Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (5 min)
2. **Setup:** Run `pip install -r requirements.txt`
3. **Validate:** Run `python validate_system.py`
4. **Train:** Run `python train_models.py`
5. **Run:** Execute `python main.py`
6. **Use:** Follow the system prompts

---

## 📚 DOCUMENTATION ROADMAP

For 5-minute overview:
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

For 10-minute status check:
→ [FINAL_STATUS.md](FINAL_STATUS.md)

For 20-minute detailed guide:
→ [WORKFLOW_UPDATED.md](WORKFLOW_UPDATED.md)

For 30-minute complete understanding:
→ [SYSTEM_FIXED_COMPLETE.md](SYSTEM_FIXED_COMPLETE.md)

For installation:
→ [SETUP_GUIDE.md](SETUP_GUIDE.md)

For technical details:
→ [README.md](README.md) & [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

**Questions?** Check the documentation files above.
**Ready to start?** Run `python main.py`

Happy Placing! 🎓
    ├── 📊 DATA COLLECTION MODULES
    ├── leetcode_dsa.py                  ← LeetCode API integration
    ├── github_project.py                ← GitHub repo analysis
    ├── aptitude_ats.py                  ← Aptitude & ATS scoring
    ├── hr_round.py                      ← HR interview evaluation
    │
    ├── 🏢 BUSINESS LOGIC
    └── company_logic.py                 ← Company hiring rules
```

---

## 📄 File Descriptions

### 🚀 Execution Files

#### main.py
- **Purpose**: Main entry point for the system
- **Usage**: `python main.py`
- **What it does**:
  - Gets student ID
  - Checks if profile exists
  - Collects missing scores (DSA, Projects, Aptitude, ATS, HR)
  - Loads/trains ML models
  - Generates predictions
  - Displays results
  - Saves to CSV

#### train_models.py
- **Purpose**: Train ML models on placement data
- **Usage**: `python train_models.py`
- **What it does**:
  - Creates sample training data
  - Initializes 4 ML models
  - Trains on student data
  - Saves models to disk
  - Prints performance metrics

#### setup.py
- **Purpose**: Initialize environment
- **Usage**: `python setup.py`
- **What it does**:
  - Checks Python version
  - Creates directories
  - Checks dependencies
  - Offers to install missing packages

---

### 📚 Documentation Files

#### README.md
**What**: Complete project documentation
**Contains**:
- Project overview
- Quick start guide
- Feature descriptions
- File structure
- Company database
- ML models explanation
- Data storage format
- Troubleshooting guide
- Model performance metrics

#### QUICKSTART.md
**What**: 3-step quick reference
**Contains**:
- Installation steps
- Score calculations overview
- Company list
- Common issues & fixes
- Pro tips
- Example run output

#### SETUP_GUIDE.md
**What**: Detailed implementation guide
**Contains**:
- Complete installation guide
- Data collection process (6 stages)
- Each module explanation
- Prediction methodology
- Probability calculation steps
- Module documentation
- Advanced features
- Performance metrics
- FAQ

#### CONFIG_GUIDE.md
**What**: Customization instructions
**Contains**:
- How to add companies
- How to modify weights
- HR question customization
- Feature engineering changes
- ML parameter tuning
- Difficulty factor adjustment
- Configuration examples
- Best practices

#### PROJECT_SUMMARY.md
**What**: Project overview
**Contains**:
- Project description
- Technical architecture
- ML methodology
- System workflow
- Performance metrics
- Learning outcomes
- What's included

#### INDEX.md (This File)
**What**: Complete file listing and descriptions
**Contains**:
- Directory structure
- File-by-file descriptions
- Module dependencies
- Import structure
- Module relationships

---

### 📦 Dependency File

#### requirements.txt
**Contains**: All Python packages needed
```
pandas==1.5.3
numpy==1.24.0
scikit-learn==1.3.0
xgboost==2.0.0
requests==2.31.0
language-tool-python==2.7.1
textstat==0.7.3
joblib==1.3.1
```

---

### 📂 Data Folder (data/)

#### student_profiles.csv
- **Status**: Auto-created on first run
- **Purpose**: Main student database
- **Columns**: Student ID, scores, predictions
- **Updates**: Every time you run `main.py`
- **Format**: CSV (Excel compatible)

#### placement_dataset_training.csv
- **Status**: Auto-created if not exists
- **Purpose**: Training data for ML models
- **Contains**: Sample placement records
- **Can be**: Replaced with your own dataset

#### campus_placement_dataset_final_academic_4000.csv
- **Purpose**: Reference dataset (optional)
- **Contains**: 4000 sample placement records
- **Usage**: For additional training if needed

#### company_profiles_with_difficulty.csv
- **Purpose**: Company information reference
- **Contains**: Company details and difficulty factors
- **Usage**: Reference data (auto-loaded by system)

#### student_profiles_100.csv
- **Purpose**: Sample student data
- **Contains**: 100 sample student records
- **Usage**: For testing and demonstration

---

### 📂 Models Folder (models/)
**Auto-created after running `train_models.py`**

#### placement_model.pkl
- **Type**: Calibrated XGBClassifier
- **Predicts**: Placement probability (0-1)
- **Features**: All student scores
- **Accuracy**: ~85%

#### salary_model.pkl
- **Type**: XGBRegressor
- **Predicts**: Salary in LPA
- **Condition**: Only on placed students
- **Range**: ±20% around prediction

#### jobrole_model.pkl
- **Type**: XGBClassifier
- **Predicts**: Job role/position
- **Classes**: SE, SDE, PM, QA, etc.
- **Output**: Most likely role

#### scaler.pkl
- **Type**: StandardScaler
- **Purpose**: Feature normalization
- **Fitted on**: Training data
- **Used by**: All predictions

#### role_encoder.pkl
- **Type**: LabelEncoder
- **Purpose**: Encode/decode job roles
- **Maps**: String roles ↔ Numeric codes

#### knn_companies.pkl
- **Type**: KNearestNeighbors
- **Purpose**: Recommend companies
- **K value**: 40 neighbors
- **Output**: Top 10 companies

#### companies_list.pkl
- **Type**: NumPy array
- **Contains**: All company names
- **Used by**: KNN model for recommendations

---

### 📂 Modules Folder (modules/)

#### student_profile.py
**Class**: `StudentProfile(student_id)`
**Methods**:
- `load_or_create_profile()` - Load/create data
- `profile_exists()` - Check if exists
- `get_profile()` - Get student data
- `save_profile(dict)` - Update CSV
- `get_missing_scores()` - Find incomplete data
**Dependencies**: pandas

#### leetcode_dsa.py
**Class**: `LeetCodeDSA(username)`
**Methods**:
- `fetch_leetcode_data()` - Get LeetCode API data
- `calculate_dsa_score()` - Compute DSA score
- `normalize()` - Normalize values
- `print_report()` - Show assessment
**Dependencies**: requests, datetime

#### github_project.py
**Class**: `GitHubProject()`
**Methods**:
- `evaluate_multiple_projects(urls)` - Analyze multiple repos
- `calculate_project_complexity(url)` - Single repo analysis
- `logic_density()` - Code complexity
- `detect_tech_usage()` - Tech stack detection
- `architecture_quality()` - Design quality
- `documentation_score()` - Doc quality
- `get_project_score()` - Final score
**Dependencies**: subprocess, os, shutil, uuid

#### aptitude_ats.py
**Class**: `AptitudeATS()`
**Methods**:
- `get_aptitude_score()` - Collect aptitude
- `get_ats_score()` - Collect ATS score
- `get_scores()` - Get both together
**Dependencies**: webbrowser

#### hr_round.py
**Class**: `HRRound()`
**Methods**:
- `conduct_interview()` - Ask 5 questions
- `communication_score()` - Evaluate communication
- `star_score()` - STAR structure scoring
- `ownership_score()` - Ownership assessment
- `confidence_consistency()` - Confidence check
- `calculate_hr_score()` - Final HR score
- `print_report()` - Show results
**Dependencies**: language_tool_python, textstat

#### feature_engineering.py
**Class**: `FeatureEngineering()`
**Methods**:
- `create_derived_features()` - Create new features
- `prepare_features()` - Scale features
- `prepare_student_input()` - Prepare single student
- `get_feature_names()` - Get feature list
**Dependencies**: pandas, sklearn.preprocessing

#### ml_models.py
**Class**: `MLModels()`
**Methods**:
- `train_models()` - Train all 4 models
- `save_models()` - Save to disk
- `load_models()` - Load from disk
**Dependencies**: xgboost, sklearn, pandas, pickle

#### company_logic.py
**Class**: `CompanyLogic()`
**Methods**:
- `check_eligibility()` - Check CGPA requirement
- `get_company_weights()` - Get feature weights
- `calculate_company_specific_score()` - Company score
- `predict_company_probability()` - Placement prob
- `get_company_type()` - Service vs Product
- `get_all_companies()` - List companies
**Features**: 15 companies with hiring logic

#### prediction.py
**Class**: `Prediction(models, logic, features)`
**Methods**:
- `predict_placement()` - Base probability
- `predict_salary()` - Salary range
- `predict_job_role()` - Role prediction
- `predict_company_probability()` - Company specific
- `get_comprehensive_prediction()` - All predictions
- `realistic_probability()` - Calibrate probs
**Dependencies**: numpy, pandas

---

## 🔄 Module Dependencies

### Import Structure
```
main.py
├── student_profile.py
├── leetcode_dsa.py
├── github_project.py
├── aptitude_ats.py
├── hr_round.py
├── ml_models.py
│   ├── xgboost
│   ├── sklearn
│   └── pickle
├── feature_engineering.py
│   ├── sklearn
│   └── pandas
├── company_logic.py
├── prediction.py
│   ├── numpy
│   └── pandas
└── train_models.py
    ├── pandas
    ├── ml_models.py
    └── feature_engineering.py
```

---

## 🔌 External APIs Used

1. **LeetCode GraphQL API**
   - Module: `leetcode_dsa.py`
   - Method: `fetch_leetcode_data()`
   - URL: https://leetcode.com/graphql
   - Purpose: Get problem-solving metrics

2. **GitHub (via Git Command)**
   - Module: `github_project.py`
   - Method: `clone_repo()`
   - Command: `git clone`
   - Purpose: Analyze repository code

3. **Web Resources (Links Only)**
   - Aptitude Test: https://aptitude-test.com/
   - Resume Checker: https://enhancv.com/resources/resume-checker/
   - Purpose: Provide user links (manual input)

---

## 🎯 Quick Navigation

### If you want to...

**Run the system**: `python main.py`

**Train models**: `python train_models.py`

**Quick reference**: Read QUICKSTART.md

**Full documentation**: Read README.md

**Setup help**: Read SETUP_GUIDE.md

**Customize system**: Read CONFIG_GUIDE.md

**Understand architecture**: Read PROJECT_SUMMARY.md

**View scores**: Open `data/student_profiles.csv`

**Modify companies**: Edit `modules/company_logic.py`

**Change HR questions**: Edit `modules/hr_round.py`

**Adjust weights**: Edit any module + `train_models.py`

---

## 📊 File Relationships

```
                    main.py
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
   student_profile  ml_models    prediction
        ↓              ↓              ↓
   CSV Database   train_models  company_logic
                       ↓
        ┌──────────┬───┴────┬──────────┐
        ↓          ↓        ↓          ↓
   LeetCode   GitHub   HR_Round   feature_eng
```

---

## ✅ All Files Present

### Core Modules (9)
- ✅ student_profile.py
- ✅ leetcode_dsa.py
- ✅ github_project.py
- ✅ aptitude_ats.py
- ✅ hr_round.py
- ✅ feature_engineering.py
- ✅ ml_models.py
- ✅ company_logic.py
- ✅ prediction.py

### Execution Files (3)
- ✅ main.py
- ✅ train_models.py
- ✅ setup.py

### Documentation (6)
- ✅ README.md
- ✅ QUICKSTART.md
- ✅ SETUP_GUIDE.md
- ✅ CONFIG_GUIDE.md
- ✅ PROJECT_SUMMARY.md
- ✅ INDEX.md

### Data Folders (2)
- ✅ data/ (auto-created)
- ✅ models/ (auto-created)

### Configuration (1)
- ✅ requirements.txt

**Total: 20 files + 2 directories = Complete Package ✅**

---

## 🚀 Getting Started Checklist

- [ ] Read QUICKSTART.md (5 min)
- [ ] Run `pip install -r requirements.txt` (2 min)
- [ ] Run `python train_models.py` (1 min)
- [ ] Run `python main.py` (10 min)
- [ ] Review data in `data/student_profiles.csv`
- [ ] Read README.md for deeper understanding
- [ ] Check CONFIG_GUIDE.md for customization

---

## 📞 Support

**Error during setup?** → See SETUP_GUIDE.md

**How to use?** → See QUICKSTART.md

**Full details?** → See README.md

**Want to customize?** → See CONFIG_GUIDE.md

**Understanding system?** → See PROJECT_SUMMARY.md

**File structure?** → You're reading it!

---

**Last Updated**: January 2026
**Version**: 1.0
**Status**: ✅ Complete

---

Happy Coding! 🎓🚀
