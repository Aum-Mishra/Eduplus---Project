# Updated Placement AI System Workflow

## System Overview
The placement prediction system now implements an **auto-fetch** workflow that intelligently manages student data through two-tier score management.

---

## Two-Tier Score Management

### **Tier 1: Academic Core Scores (PERMANENT)**
These scores are collected once and remain constant:
- **CGPA** - Overall GPA
- **OS Score** - Operating Systems
- **DBMS Score** - Database Management Systems
- **CN Score** - Computer Networks
- **OOP Score** - Object-Oriented Programming
- **System Design Score** - System Design concepts
- **CS Fundamentals Score** - General CS knowledge
- **Hackathon Wins** - Number of hackathons won

### **Tier 2: Variable Skill Scores (UPDATABLE)**
These scores can be re-evaluated/updated:
- **DSA Score** - Data Structures & Algorithms (from LeetCode)
- **Project Score** - Project work quality (from GitHub)
- **Aptitude Score** - Reasoning & aptitude test
- **HR Score** - HR round interview performance
- **Resume ATS Score** - Resume screening match

---

## Workflow Logic

### **Step 1: Student ID Entry**
```
Enter Student ID → System checks if profile exists
```

### **Step 2A: EXISTING Student Profile Found**
```
✅ Profile Found
  ↓
1. Auto-fetch Academic Scores (display read-only)
   - CGPA, OS, DBMS, CN, OOP, System Design, CS Fundamentals, Hackathons
  ↓
2. Show Current Variable Scores
   - DSA, Project, Aptitude, HR, Resume ATS
  ↓
3. Ask User: "Update skill scores? (y/n)"
   
   IF YES:
   ├─ Collect new DSA score (LeetCode/Manual)
   ├─ Collect new Project score (GitHub/Manual)
   ├─ Collect new Aptitude score (Test)
   ├─ Collect new HR score (Interview)
   └─ Collect new ATS score (Resume check)
   
   IF NO:
   └─ Use existing scores from CSV
  ↓
4. Auto-fetch all 12 scores to prediction model
  ↓
5. Generate predictions automatically
  ↓
6. Display results (placement%, salary, role, companies)
  ↓
7. Save updated data to CSV
```

### **Step 2B: NEW Student Profile**
```
❌ Profile Not Found
  ↓
1. Collect Academic Information (ONE TIME)
   - CGPA, OS, DBMS, CN, OOP, System Design, CS Fundamentals, Hackathons
  ↓
2. Collect Variable Skill Scores
   - DSA score (LeetCode/Manual)
   - Project score (GitHub/Manual)
   - Aptitude score (Test)
   - HR score (Interview)
   - ATS score (Resume check)
  ↓
3. Save profile to CSV with all 12 scores
  ↓
4. Auto-fetch all 12 scores to prediction model
  ↓
5. Generate predictions automatically
  ↓
6. Display results
  ↓
7. Store predictions in CSV
```

---

## Data Flow Diagram

```
MAIN PROGRAM
    ↓
[Get Student ID]
    ↓
[Check CSV: profile_exists()?]
    ├─ YES → [Display Academic + Variable Scores]
    │        [Ask: Update variable scores?]
    │        ├─ YES → [Collect 5 variable scores]
    │        └─ NO  → [Use existing scores]
    │
    └─ NO  → [Collect 7 academic scores once]
             [Collect 5 variable scores]
             [Save to CSV]
    ↓
[Auto-fetch all 12 scores + hackathons]
    ↓
[FEATURE ENGINEERING]
    ├─ Normalize scores
    ├─ Create derived features
    └─ Prepare for ML model
    ↓
[ML MODEL PREDICTION]
    ├─ Placement Classifier
    ├─ Salary Regressor
    ├─ Job Role Classifier
    └─ Company Recommender (KNN)
    ↓
[POST-PROCESSING]
    ├─ Calculate probabilities
    ├─ Determine salary range
    ├─ Recommend top companies
    └─ Assess company type preference
    ↓
[DISPLAY RESULTS]
    ├─ Placement probability
    ├─ Expected salary (LPA)
    ├─ Job role prediction
    ├─ Company type probability
    └─ Top 10 company recommendations
    ↓
[UPDATE CSV]
    └─ Save predictions to student profile
```

---

## CSV Database Schema

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| student_id | INT | Unique student ID | 101 |
| **cgpa** | FLOAT | Overall GPA | 8.5 |
| **os_score** | FLOAT | Operating Systems | 85.0 |
| **dbms_score** | FLOAT | Database Systems | 88.0 |
| **cn_score** | FLOAT | Computer Networks | 82.0 |
| **oop_score** | FLOAT | Object-Oriented Programming | 90.0 |
| **system_design_score** | FLOAT | System Design | 75.0 |
| **cs_fundamentals_score** | FLOAT | CS Fundamentals | 87.0 |
| dsa_score | FLOAT | Data Structures & Algorithms | 78.5 |
| project_score | FLOAT | GitHub Project Quality | 82.0 |
| aptitude_score | FLOAT | Aptitude Test | 80.0 |
| hr_score | FLOAT | HR Interview | 85.0 |
| resume_ats_score | FLOAT | ATS Score | 88.0 |
| hackathon_wins | INT | Hackathon Participations | 2 |
| placement_probability | FLOAT | Predicted placement % | 92.5 |
| expected_salary | FLOAT | Expected salary (LPA) | 12.5 |
| predicted_job_role | STRING | Predicted job role | "Software Engineer" |
| service_company_prob | FLOAT | Service company probability | 55.0 |
| product_company_prob | FLOAT | Product company probability | 45.0 |

**Bold columns** = Academic core scores (permanent)
**Regular columns** = Variable scores (updatable)

---

## Key Features

### ✅ **Auto-Fetch Capability**
- System automatically retrieves existing profile from CSV
- No need to re-enter academic information
- Scores are automatically passed to ML model

### ✅ **Selective Updates**
- Only variable scores (DSA, Projects, Aptitude, HR, ATS) can be updated
- Academic scores remain constant (CGPA, core subjects)
- User chooses whether to update or keep existing scores

### ✅ **Automatic Prediction**
- Once data is complete, prediction happens automatically
- No manual model invocation required
- Results displayed immediately

### ✅ **Data Persistence**
- All student data stored in CSV database
- Predictions automatically saved
- Historical data available for analysis

### ✅ **Intelligent Collection**
- New students: collect all 12 scores
- Returning students: collect only updated variable scores
- Manual fallback if API services (LeetCode, GitHub) unavailable

---

## Usage Example

### **Scenario 1: New Student**
```
Enter Student ID: 101

📝 Creating new student profile...

📚 ACADEMIC INFORMATION
Enter CGPA (0-10): 8.5
Enter OS Score (0-100): 85
[... collect other academic scores ...]
Enter Hackathon Wins (0-5): 2

🎯 SKILL ASSESSMENT

1️⃣ DSA SCORE (From LeetCode)
Enter your LeetCode username: john_coder
[Fetches LeetCode data...]
DSA Score: 78.5

2️⃣ PROJECT SCORE (From GitHub)
How many repositories? 2
[Evaluates GitHub projects...]
Project Score: 82.0

[... collect aptitude, ATS, HR scores ...]

🔮 GENERATING PREDICTIONS
[ML models process data...]

📈 PLACEMENT PREDICTION RESULTS
Overall Placement Probability: 92.5%
Expected Salary: ₹12.5 LPA
Predicted Job Role: Software Engineer
Service Companies: 55%
Product Companies: 45%
Top Companies: Google, Microsoft, Flipkart...

✅ Profile saved!
```

### **Scenario 2: Returning Student**
```
Enter Student ID: 101

✅ Student profile found!

📚 Current Academic Information:
  CGPA: 8.5
  OS Score: 85
  [... other scores ...]

🎯 Current Skill Scores:
  DSA Score: 78.5
  Project Score: 82.0
  Aptitude Score: 80.0
  HR Score: 85.0
  Resume ATS Score: 88.0

❓ Update skill scores? (y/n): y

🔄 Updating skill scores...
1️⃣ DSA SCORE (From LeetCode)
Enter your LeetCode username: john_coder
[New DSA Score: 85.0]

[... update other variable scores ...]

📈 PLACEMENT PREDICTION RESULTS
[Updated predictions generated...]

✅ Profile updated!
```

---

## System Architecture

```
main.py (Orchestration)
    ├─ student_profile.py (Data Management)
    │   ├─ load_or_create_profile()
    │   ├─ profile_exists()
    │   ├─ get_academic_scores()
    │   ├─ get_variable_scores()
    │   ├─ save_profile()
    │   └─ data/student_profiles.csv
    │
    ├─ [Data Collection Modules]
    │   ├─ leetcode_dsa.py
    │   ├─ github_project.py
    │   ├─ aptitude_ats.py
    │   └─ hr_round.py
    │
    ├─ feature_engineering.py (Feature Prep)
    │
    ├─ ml_models.py (Model Loading)
    │   ├─ placement_model
    │   ├─ salary_model
    │   ├─ jobrole_model
    │   └─ knn_companies
    │
    └─ prediction.py (Prediction Engine)
        └─ get_comprehensive_prediction()
```

---

## Running the System

### **Start the Application**
```bash
python main.py
```

### **Train Models (if needed)**
```bash
python train_models.py
```

---

## Important Notes

1. **Academic scores are permanent** - Once entered, they're not collected again
2. **Variable scores are optional updates** - User chooses whether to update or keep existing
3. **Auto-fetch ensures data consistency** - All scores retrieved from CSV for predictions
4. **Predictions are automatic** - Happens immediately after data collection
5. **CSV is the source of truth** - All data persisted for future reference

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| LeetCode API fails | System falls back to manual DSA score entry |
| GitHub API fails | System falls back to manual project score entry |
| CSV file not found | System creates new CSV with correct schema automatically |
| Profile not loading | Check `data/student_profiles.csv` exists and has correct headers |

---

## Data Flow Summary

✅ **Student ID** → Check CSV → Fetch Academic Scores → Show Variable Scores → Ask Update? → Collect/Update → Auto-fetch All Scores → ML Models → Predictions → Display Results → Save to CSV

