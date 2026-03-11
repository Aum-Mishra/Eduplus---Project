# ⚡ QUICK START GUIDE - Placement AI System v2.0

## 🎯 What This System Does

Automatically predicts job placement, salary, job role, and suitable companies based on student academic and skill scores.

---

## 🚀 QUICK SETUP (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Train Models (First Time Only)
```bash
python train_models.py
```
⏱️ Takes ~2-5 minutes depending on your computer

### Step 3: Run the System
```bash
python main.py
```

---

## 📊 TWO SCENARIOS

### **Scenario A: BRAND NEW STUDENT**

```
1. Enter your Student ID: [TYPE YOUR ID]

2. System shows: "Creating new student profile..."

3. Enter ACADEMIC SCORES (one time only):
   - CGPA
   - OS Score
   - DBMS Score
   - CN Score
   - OOP Score
   - System Design Score
   - CS Fundamentals Score
   - Hackathon Wins

4. Enter SKILL SCORES:
   - DSA Score (from LeetCode or manual)
   - Project Score (from GitHub or manual)
   - Aptitude Score (from test)
   - HR Score (from interview)
   - Resume ATS Score (from resume check)

5. System automatically generates predictions
   - Shows placement probability
   - Shows expected salary
   - Recommends suitable companies
   - Saves everything to database

DONE! ✅
```

---

### **Scenario B: RETURNING STUDENT**

```
1. Enter your Student ID: [TYPE YOUR ID]

2. System shows: "Student profile found!"
   - Displays all your academic scores (READ ONLY)
   - Shows your current skill scores

3. Asked: "Update skill scores? (y/n)"

   IF YES (y):
   └─ Re-enter 5 skill scores (DSA, Projects, Aptitude, HR, ATS)
      System will re-fetch from LeetCode/GitHub if available

   IF NO (n):
   └─ Uses existing scores

4. System automatically generates updated predictions
   - New placement probability based on new skills
   - Recalculated salary prediction
   - Updated company recommendations

DONE! ✅
```

---

## 💾 DATA STORED IN CSV

**File Location:** `data/student_profiles.csv`

| Your Score | Type | How to Provide |
|------------|------|----------------|
| **CGPA** | Academic (Permanent) | Enter manually |
| **OS Score** | Academic (Permanent) | Enter manually |
| **DBMS Score** | Academic (Permanent) | Enter manually |
| **CN Score** | Academic (Permanent) | Enter manually |
| **OOP Score** | Academic (Permanent) | Enter manually |
| **System Design** | Academic (Permanent) | Enter manually |
| **CS Fundamentals** | Academic (Permanent) | Enter manually |
| **Hackathon Wins** | Academic (Permanent) | Enter manually |
| **DSA Score** | Skill (Can Update) | LeetCode username or manual |
| **Project Score** | Skill (Can Update) | GitHub URLs or manual |
| **Aptitude Score** | Skill (Can Update) | Automated test |
| **HR Score** | Skill (Can Update) | Interview questions |
| **Resume ATS** | Skill (Can Update) | Resume analysis |

---

## 🎓 Score Ranges

**All scores are 0-100 (except CGPA which is 0-10)**

- **0-40:** Poor
- **40-60:** Average
- **60-80:** Good
- **80-100:** Excellent

---

## 📈 PREDICTION OUTPUTS

After entering data, you get:

1. **Placement Probability** (%)
   - How likely you are to get placed
   - Example: 92.5%

2. **Expected Salary** (₹ LPA)
   - Predicted annual package
   - With salary range
   - Example: ₹12.5 LPA (₹11.2 - ₹14.8)

3. **Job Role Prediction**
   - Type of job you're likely to get
   - Example: "Software Engineer"

4. **Company Type Probability**
   - Service Company: 55%
   - Product Company: 45%

5. **Top 10 Recommended Companies**
   - Sorted by probability
   - Example: Google 89%, Microsoft 87%, Amazon 83%, etc.

---

## 🔄 TYPICAL USER JOURNEY

```
First Visit:
├─ Enter Student ID
├─ "Profile not found" ← System creates new profile
├─ Collect 7 academic scores
├─ Collect 5 skill scores
├─ Get predictions ✨
├─ Data saved to CSV
└─ Exit

Second Visit (3 months later):
├─ Enter Student ID
├─ "Profile found!" ← Auto-fetches academic scores
├─ Shows current skill scores
├─ Ask: "Update skills?" → YES
├─ Re-enter 5 skill scores (improved!)
├─ Get updated predictions ✨
├─ Data updated in CSV
└─ Exit

Third Visit (after interview prep):
├─ Enter Student ID
├─ "Profile found!"
├─ Ask: "Update skills?" → YES
├─ Update only skill scores
├─ Get new predictions ✨
└─ Exit
```

---

## ✅ VALIDATION BEFORE RUNNING

Check if everything is set up correctly:

```bash
python validate_system.py
```

Should show:
- ✅ All files present
- ✅ All modules found
- ✅ CSV schema correct
- ✅ Packages installed

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError" | Run: `pip install -r requirements.txt` |
| "No module named 'pandas'" | Run: `pip install pandas xgboost scikit-learn` |
| "CSV file not found" | Run: `python main.py` once (creates CSV automatically) |
| "Models not found" | Run: `python train_models.py` |
| "LeetCode fetch failed" | Enter DSA score manually when prompted |
| "GitHub fetch failed" | Enter project score manually when prompted |

---

## 📞 NEED HELP?

1. **Check Documentation:**
   - `README.md` - Full system overview
   - `WORKFLOW_UPDATED.md` - Detailed workflow explanation
   - `SYSTEM_FIXED_COMPLETE.md` - Complete implementation details

2. **Validate Setup:**
   - Run: `python validate_system.py`

3. **Check CSV Data:**
   - Open: `data/student_profiles.csv` with Excel or text editor
   - Verify your scores are saved

4. **Check Models:**
   - Open: `models/` directory
   - Should have `.pkl` files if trained

---

## 🎮 EXAMPLE SESSION

```
$ python main.py

⭐ PLACEMENT AI PREDICTION SYSTEM ⭐

Enter Student ID: 101

❌ Profile not found

📝 Creating new student profile...

📚 ACADEMIC INFORMATION
Enter CGPA (0-10): 8.5
Enter OS Score (0-100): 85
Enter DBMS Score (0-100): 88
Enter CN Score (0-100): 82
Enter OOP Score (0-100): 90
Enter System Design Score (0-100): 75
Enter CS Fundamentals Score (0-100): 87
Enter Hackathon Wins (0-5): 2

🎯 SKILL ASSESSMENT

1️⃣ DSA SCORE (From LeetCode)
Enter your LeetCode username: john_coder
[Fetches data... analyzing...]
DSA Score: 78.5

2️⃣ PROJECT SCORE (From GitHub)
How many GitHub repositories? 1
Enter GitHub repo URL 1: https://github.com/john/ecommerce
[Analyzing code quality...]
Project Score: 82.0

3️⃣ APTITUDE & ATS SCORES
[Running tests...]
Aptitude Score: 80.0
ATS Score: 88.0

4️⃣ HR ROUND INTERVIEW
[Questions asked...]
HR Score: 85.0

⏳ LOADING DATA FOR PREDICTION

🔮 GENERATING PREDICTIONS

📈 PLACEMENT PREDICTION RESULTS
👤 Student ID: 101
🎯 Overall Placement Probability: 92.5%
💼 Service-Based Companies: 55.0%
💰 Expected Salary: ₹12.5 LPA (₹11.2 - ₹14.8)
🧑‍💼 Predicted Job Role: Software Engineer
🏆 Top Companies: Google, Microsoft, Flipkart...

✅ All operations completed successfully!
📁 Data saved to: data/student_profiles.csv
```

---

## 🌟 KEY FEATURES

✅ **Auto-Fetch** - Remembers your data, no re-entry needed
✅ **Smart Updates** - Only update skills, not academic scores
✅ **Instant Predictions** - Get results immediately
✅ **Company Suggestions** - 10 top recommended companies
✅ **Salary Estimates** - Predicted package with range
✅ **Job Role Prediction** - What type of job to expect
✅ **Probability Scores** - Service vs Product company likelihood
✅ **Data Persistence** - Everything saved in database

---

## 📋 REQUIREMENTS

- **Python:** 3.7+
- **Storage:** ~500 MB (for models + data)
- **Internet:** Optional (for LeetCode/GitHub API, has manual fallback)
- **Dependencies:** See requirements.txt

---

## 🎯 NEXT STEPS

1. ✅ Install dependencies
2. ✅ Train models (first time)
3. ✅ Run main.py
4. ✅ Enter your data
5. ✅ Get predictions!
6. ✅ Check results in CSV

**Ready? Type:** `python main.py`

