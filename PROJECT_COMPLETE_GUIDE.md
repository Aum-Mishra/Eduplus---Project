# Eduplus Campus Placement System - Complete Project Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [ML Models Explained](#ml-models-explained)
4. [System Components](#system-components)
5. [Data Pipeline](#data-pipeline)
6. [API Reference](#api-reference)
7. [File Structure](#file-structure)
8. [Technology Stack](#technology-stack)

---

## Project Overview

**Eduplus** is an intelligent campus placement system that uses machine learning and conversational AI to:
- Predict student placement probability
- Estimate salary packages
- Recommend suitable job roles
- Suggest matching companies
- Classify salary tiers
- Provide career guidance via chatbot

The system combines **5 independent ML models**, a **Flask backend API**, a **Rasa-powered chatbot**, and a **React frontend** into a unified platform for student career counseling.

### Key Features
- ✅ **5 ML Models** for different predictions
- ✅ **REST API** for all predictions
- ✅ **Conversational Chatbot** (Rasa)
- ✅ **Real-time Processing** with caching
- ✅ **Comprehensive Reports** and analytics
- ✅ **Interactive Dashboard** with visualizations
- ✅ **Company Database** with difficulty ratings
- ✅ **Feedback Loop** for model improvement

---

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────┐
│                  React Frontend :5173                    │
│           (Dashboard, Charts, Reports, Chat)            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ Flask   │   │   Rasa   │   │   LLM    │
    │ API     │   │ Chatbot  │   │ Service  │
    │ :5000   │   │ :5005    │   │ :8001    │
    └────┬────┘   └──────────┘   └──────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   5 ML Models (XGBoost, scikit-learn)   │
├─────────────────────────────────────────┤
│ 1. Placement Probability                │
│ 2. Salary Value (Regression)            │
│ 3. Job Role Classification              │
│ 4. Company Recommendations (KNN)        │
│ 5. Salary Tier Classification           │
└────────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  Data & Models  │
    ├─────────────────┤
    │ .pkl files      │
    │ CSV datasets    │
    │ Student profiles│
    │ Company profiles│
    └─────────────────┘
```

### Service Orchestration

```
Terminal 1: Flask API (:5000)
           ↓
           Loads all 5 ML models
           Provides prediction endpoints
           Manages student data

Terminal 2: LLM Service (:8001)
           ↓
           Provides text generation
           Career guidance summaries

Terminal 3: Rasa Action Server (:5055)
           ↓
           Handles custom actions
           Database queries

Terminal 4: Rasa HTTP Server (:5005)
           ↓
           Conversational AI
           Intent recognition
           Entity extraction

Terminal 5: Frontend Dev Server (:5173)
           ↓
           React + Vite
           Interactive dashboard
           Real-time updates
```

---

## ML Models Explained

### 1. **Placement Probability Model**
**Purpose:** Predict if a student will get placed (Binary Classification)

**Algorithm:** CalibratedClassifierCV + XGBoost
```
Inputs:  Student profile (CGPA, skills, internships, etc.)
Output:  Probability of placement (0-1)
```

**How It Works:**
1. XGBoost classifier trains on historical placement data
2. CalibratedClassifierCV calibrates probabilities for reliability
3. Returns 0.85 = 85% chance of placement

**File:** `models/placement_model.pkl`
**Training:** `train_models.py`

**API Endpoint:**
```python
POST /api/predictions/generate
{
  "student_profile": {...},
  "models": "all"
}
# Response includes: placement_probability
```

---

### 2. **Salary Value Model**
**Purpose:** Predict actual salary package (Regression)

**Algorithm:** XGBRegressor
```
Inputs:  Student profile + company data
Output:  Predicted salary in LPA (lakhs per annum)
```

**How It Works:**
1. Trained on historical salary data
2. Considers student skills, experience, company size
3. Returns value like 8.5 LPA

**File:** `models/salary_model.pkl`
**Training:** `train_models.py`

**Output Range:** 4-50+ LPA (depending on company and skills)

---

### 3. **Job Role Classification Model**
**Purpose:** Recommend suitable job role for student

**Algorithm:** XGBClassifier + LabelEncoder
```
Inputs:  Student profile
Output:  Job role classification
         (Software Engineer, Data Analyst, DevOps, etc.)
```

**How It Works:**
1. Maps student skills to predefined job roles
2. Considers educational background and interests
3. Returns top matching role

**File:** `models/job_role_model.pkl`
**Training:** `train_models.py`

**Possible Roles:**
- Software Developer
- Data Scientist
- Quality Assurance
- DevOps Engineer
- Business Analyst
- etc.

---

### 4. **Company Recommendations Model**
**Purpose:** Find matching companies for student

**Algorithm:** K-Nearest Neighbors (KNN)
```
Inputs:  Student profile
Output:  Top 5 matching companies
```

**How It Works:**
1. Builds feature vectors for students and companies
2. Uses KNN to find similar companies
3. Considers company difficulty rating
4. Filters by skills match

**Data Source:** `company_profiles_with_difficulty.csv`
**Distance Metric:** Euclidean distance
**K Value:** 5 (top 5 recommendations)

**Company Attributes:**
- Name, location, industry
- Required skills
- Difficulty rating (1-10)
- Historical placement stats

---

### 5. **Salary Tier Classification Model**
**Purpose:** Classify salary into categories

**Algorithm:** XGBClassifier (Multiclass)
```
Inputs:  Student profile + company
Output:  Salary tier category
         (Tier1, Tier2, Tier3, etc.)
```

**How It Works:**
1. Predicts salary bracket (categorical)
2. Classifies into tiers:
   - **Tier 1:** 0-4 LPA
   - **Tier 2:** 4-8 LPA
   - **Tier 3:** 8-12 LPA
   - **Tier 4:** 12-20 LPA
   - **Tier 5:** 20+ LPA

**File:** `models/salary_tier_model.pkl`
**Training:** `train_salary_model.py`

---

## System Components

### 1. Flask Backend (app.py)

**Purpose:** Main API server providing predictions and data management

**Key Routes:**

#### Prediction Endpoints
```python
POST /api/predictions/generate
    Input: Student profile (CGPA, skills, internships, etc.)
    Output: All 5 model predictions
    
POST /api/predictions/placement
    Input: Student profile
    Output: Placement probability only
    
POST /api/predictions/salary
    Input: Student profile + company
    Output: Salary prediction
    
POST /api/predictions/role
    Input: Student profile
    Output: Recommended job role
    
POST /api/recommendations/companies
    Input: Student profile
    Output: Top 5 matching companies
    
POST /api/recommendations/salary-tier
    Input: Student profile
    Output: Salary tier classification
```

#### Data Management
```python
GET /api/students
    Retrieve all students

POST /api/students
    Add new student profile

GET /api/students/<id>
    Get student details

PUT /api/students/<id>
    Update student data

GET /api/companies
    List all companies

GET /api/companies/<id>
    Company details with history
```

#### Report Endpoints
```python
GET /api/reports/placement-summary
    Overall placement statistics

GET /api/reports/salary-analysis
    Salary distribution and trends

GET /api/reports/company-performance
    Company-wise placement data

GET /api/reports/student/<id>
    Individual student report
```

#### Chatbot Integration
```python
POST /api/chat
    Receive message and context
    Return: Chatbot response via Rasa
```

**Technology:** Flask 3.0.3, Python 3.10
**Database:** CSV files + pickle models

---

### 2. Rasa Chatbot

**Purpose:** Conversational AI for career guidance and Q&A

**Architecture:**
```
User Input → NLU (Intent + Entities) → Dialogue Management → Action Server → Response
```

**Key Intents:**
- `greet` - Welcome user
- `placement_probability` - Ask about placement chances
- `salary_estimation` - Ask salary prediction
- `company_recommendation` - Request company suggestions
- `job_role_suggestion` - Ask for suitable roles
- `faq` - Frequently asked questions
- `goodbye` - Exit chat

**Entities:**
- `STUDENT_ID` - Student identifier
- `COMPANY_NAME` - Company name
- `SKILL` - Technical skill
- `BRANCH` - Educational branch

**Dialogue Management:**
1. Recognizes user intent
2. Extracts relevant entities
3. Calls appropriate Flask API endpoint
4. Formats response in natural language
5. Returns to user

**Action Server (port 5055):**
- Custom Python actions
- Database queries
- Model inference calls
- Response formatting

**HTTP Server (port 5005):**
- Receives messages
- Returns responses
- Maintains conversation history
- Provides intent scores

**Training Data:**
- `Chatbot/data/nlu.yml` - Training phrases
- `Chatbot/data/stories.yml` - Dialogue flows
- `Chatbot/data/rules.yml` - Hard rules
- `Chatbot/domain.yml` - Intents, entities, actions

---

### 3. React Frontend (UI Eduplus)

**Purpose:** Interactive dashboard for student career counseling

**Technology:** React 18, TypeScript, Vite, TailwindCSS

**Key Pages:**

#### Dashboard (Main View)
- Student profile display
- Quick prediction summary
- Recent activity
- Recommended companies
- Navigation menu

#### Predictions Page
- Input student details
- View all 5 model predictions
- Visual comparison
- Historical tracking

#### Companies Page
- Browse company database
- Filter by difficulty/skills
- View company details
- Placement statistics

#### Reports Page
- Placement trends
- Salary analysis
- Company performance
- Student statistics

#### Chat Page
- Interactive chatbot
- Conversation history
- Quick action buttons
- Suggested questions

#### Settings Page
- User preferences
- Data management
- Account settings

**State Management:** React Context API
**Styling:** TailwindCSS
**HTTP Client:** Axios
**Charting:** Chart.js or similar

---

### 4. LLM Service (llm_isolated_service/app.py)

**Purpose:** Additional text generation capabilities

**Features:**
- Summarization
- Text generation
- Career guidance summaries
- Report generation

**Port:** 8001
**Framework:** Flask or FastAPI

---

## Data Pipeline

### Training Data Flow

```
Raw Data
    ├─ student_profiles.csv (student data)
    ├─ campus_placement_dataset.csv (historical data)
    └─ company_profiles_with_difficulty.csv (company data)
    
    ↓ (Feature Engineering)
    
Feature Engineering (modules/feature_engineering.py)
    ├─ Normalize CGPA (0-10 → 0-1)
    ├─ Encode categorical variables
    ├─ Scale numerical features
    └─ Handle missing values
    
    ↓ (Training)
    
Model Training (train_models.py)
    ├─ Split data (80% train, 20% test)
    ├─ Train each model
    ├─ Evaluate metrics
    └─ Save as .pkl files
    
    ↓ (Output)
    
Trained Models (models/)
    ├─ placement_model.pkl
    ├─ salary_model.pkl
    ├─ job_role_model.pkl
    ├─ company_knn_model.pkl
    └─ salary_tier_model.pkl
```

### Prediction Flow

```
User Input (Student Profile)
    ├─ CGPA, skills, internships
    ├─ Projects, certifications
    └─ Interests, branch, batch
    
    ↓ (Flask API)
    
Feature Transformation
    ├─ Normalize values
    ├─ Encode categorical
    └─ Scale features
    
    ↓ (Model Loading)
    
Load Trained Models from Disk
    ├─ placement_model.pkl
    ├─ salary_model.pkl
    ├─ job_role_model.pkl
    ├─ company_knn_model.pkl
    └─ salary_tier_model.pkl
    
    ↓ (Inference)
    
Generate Predictions
    ├─ Calculate probabilities
    ├─ Get salary estimate
    ├─ Predict job role
    ├─ Find companies (KNN)
    └─ Classify salary tier
    
    ↓ (Response)
    
Return Results to Frontend
    ├─ JSON format
    ├─ Visualizations
    └─ Recommendations
```

### Data Storage

```
data/
├─ campus_placement_dataset_final_academic_4000.csv
│  └─ 4000 historical student records
│
├─ company_profiles_with_difficulty.csv
│  └─ Company database with difficulty ratings
│
└─ student_profiles_100.csv
   └─ Current student data

models/
├─ placement_model.pkl         (Binary classification)
├─ salary_model.pkl            (Regression)
├─ job_role_model.pkl          (Classification)
├─ company_knn_model.pkl       (KNN model + scaler)
└─ salary_tier_model.pkl       (Multiclass)
```

---

## API Reference

### Core Prediction API

#### 1. Generate All Predictions
```bash
POST /api/predictions/generate
Content-Type: application/json

{
  "student_id": "STU001",
  "cgpa": 8.5,
  "skills": ["Python", "Java", "SQL"],
  "internships": 1,
  "projects": 3,
  "certifications": ["AWS", "DataAnalytics"],
  "branch": "CSE",
  "batch": 2024
}

Response (200 OK):
{
  "placement_probability": 0.85,
  "predicted_salary": 8.5,
  "job_role": "Software Developer",
  "recommended_companies": [
    {"name": "TCS", "difficulty": 5, "match": 0.92},
    {"name": "Infosys", "difficulty": 4, "match": 0.88},
    ...
  ],
  "salary_tier": "Tier 3 (8-12 LPA)",
  "timestamp": "2024-08-08T10:30:00Z"
}
```

#### 2. Company Recommendations
```bash
POST /api/recommendations/companies
{
  "student_id": "STU001",
  "skills": ["Python", "Java"],
  "max_difficulty": 8
}

Response:
{
  "companies": [
    {
      "name": "TCS",
      "difficulty": 5,
      "skills_match": ["Python"],
      "placement_rate": 0.92,
      "avg_salary": 8.5
    },
    ...
  ]
}
```

#### 3. Placement Probability
```bash
POST /api/predictions/placement
{
  "student_profile": {...}
}

Response:
{
  "placement_probability": 0.85,
  "confidence": 0.92,
  "likelihood_category": "High"
}
```

---

## File Structure

```
Eduplus/
│
├── app.py                              # Main Flask backend
├── train_models.py                     # ML model training script
├── train_salary_model.py               # Salary model training
├── update_profiles.py                  # Data update script
├── evaluate_ml_models_report.py        # Model evaluation
├── validate_system.py                  # System validation
│
├── data/                               # Datasets
│   ├── campus_placement_dataset_final_academic_4000.csv
│   ├── company_profiles_with_difficulty.csv
│   └── student_profiles_100.csv
│
├── models/                             # Trained ML models (.pkl files)
│   ├── placement_model.pkl
│   ├── salary_model.pkl
│   ├── job_role_model.pkl
│   ├── company_knn_model.pkl
│   └── salary_tier_model.pkl
│
├── modules/                            # Python modules
│   ├── ml_models.py                    # ML model manager class
│   ├── feature_engineering.py          # Feature preprocessing
│   ├── aptitude_ats.py                 # Aptitude calculations
│   ├── hr_round.py                     # HR round simulation
│   ├── leetcode_dsa.py                 # DSA/Coding assessment
│   ├── github_project.py               # GitHub profile analysis
│   └── service_product_probability.py  # Service/Product probability
│
├── Chatbot/                            # Rasa chatbot
│   ├── config.yml                      # Rasa configuration
│   ├── domain.yml                      # Intents, entities, actions
│   ├── data/
│   │   ├── nlu.yml                     # NLU training data
│   │   ├── stories.yml                 # Dialogue stories
│   │   └── rules.yml                   # Dialogue rules
│   ├── actions/
│   │   └── actions.py                  # Custom actions
│   └── models/
│       └── current.tar.gz              # Trained Rasa model
│
├── UI Eduplus/                         # React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── App.tsx                 # Main app component
│   │   │   ├── components/
│   │   │   │   ├── Dashboard.tsx       # Dashboard page
│   │   │   │   ├── Predictions.tsx     # Predictions page
│   │   │   │   ├── Companies.tsx       # Companies page
│   │   │   │   └── Chat.tsx            # Chatbot page
│   │   │   └── utils/
│   │   ├── main.tsx                    # Entry point
│   │   └── index.css                   # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── llm_isolated_service/               # Additional LLM service
│   └── app.py
│
├── .venv_all/                          # Python virtual environment
│
├── requirements.txt                    # Python dependencies
├── setup_system.ps1                    # Windows setup script
├── setup.py                            # Python package setup
│
└── README.md                           # Documentation
```

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10.x | Core language |
| Flask | 3.0.3 | REST API framework |
| XGBoost | 2.0.0 | ML models |
| scikit-learn | 1.1.3 | Feature preprocessing |
| pandas | 2.1.4 | Data manipulation |
| numpy | 1.24.3 | Numerical computing |
| joblib | 1.2.0 | Model serialization |
| Rasa | 3.6.13 | Conversational AI |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool |
| TailwindCSS | 3.x | Styling |
| Axios | 1.x | HTTP client |

### Environment
| Technology | Purpose |
|-----------|---------|
| Windows PowerShell | Setup automation |
| Node.js | Frontend build |
| pip | Package management |
| Virtual Environment | Dependency isolation |

---

## System Requirements

### Hardware
- **CPU:** Intel i5 or equivalent (2+ cores)
- **RAM:** 8 GB minimum, 16 GB recommended
- **Storage:** 5 GB for code + data + models

### Software
- **OS:** Windows 10+ (for PowerShell scripts)
- **Python:** 3.10.x (required for Rasa compatibility)
- **Node.js:** 16+ (for frontend)
- **npm:** 8+ (package management)

### Network
- Internet connection (one-time for downloads)
- Localhost ports: 5000, 5005, 5055, 5173, 8001

---

## Getting Started

### Quick Setup
1. See `SETUP_AND_STARTUP_GUIDE.md` for detailed instructions
2. Run: `.\setup_system.ps1 -SetupOnly`
3. Run: `.\setup_system.ps1 -RunOnly`
4. Access: http://localhost:5173

### For Developers
1. Install Python 3.10 and Node.js
2. Clone repository
3. Create virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Train models: `python train_models.py`
6. Run services: `.\setup_system.ps1 -RunOnly`

---

## Common Operations

### Train ML Models
```bash
# Train all models
python train_models.py

# Train only salary model
python train_salary_model.py

# Evaluate models
python evaluate_ml_models_report.py
```

### Test Predictions
```bash
# Validate system
python validate_system.py

# Generate sample report
python evaluate_ml_models_report.py
```

### Update Data
```bash
# Update student/company profiles
python update_profiles.py
```

---

## Troubleshooting

### Models Not Found
- Run `python train_models.py` to train models
- Check `models/` directory for .pkl files

### Rasa Model Issues
- Delete `Chatbot/models/` folder
- Run `.\setup_system.ps1 -SetupOnly` to retrain

### Port Already in Use
- Change port in respective service
- Or close conflicting application

### Frontend Not Loading
- Check `npm run dev` output
- Verify port 5173 is available

---

## Documentation
- **This File:** Project overview and architecture
- **SETUP_AND_STARTUP_GUIDE.md:** Step-by-step setup and running
- **Project Summary:** PROJECT_SUMMARY.md
- **API Details:** Endpoints documented in app.py
- **ML Models:** Detailed in modules/ml_models.py

---

**Created:** August 2025
**Version:** 1.0
**Status:** Production Ready

For questions or contributions, refer to individual component documentation.
