# ⚡ Quick Start Guide

## 🚀 Get Running in 3 Steps

### Step 1: Install Dependencies (2 minutes)
```bash
pip install -r requirements.txt
```

### Step 2: Train Models (1 minute) - First Time Only
```bash
python train_models.py
```

### Step 3: Run the System (10-15 minutes)
```bash
python main.py
```

---

## 📋 What Happens When You Run

### Input Collection
```
1. Student ID
2. CGPA & Fundamentals
3. LeetCode Username (for DSA)
4. GitHub Repos (for Projects)
5. Aptitude Score (manual)
6. ATS Score (manual)
7. HR Interview (5 questions)
```

### Output You Get
```
✅ Placement Probability: X%
✅ Salary Range: ₹XX - ₹YY LPA
✅ Expected Job Role: SE/SDE/PM
✅ Service Company Prob: X%
✅ Product Company Prob: Y%
✅ Top 10 Companies with scores
```

---

## 📁 File Structure

```
placement_ai_system/
├── data/
│   ├── student_profiles.csv       ← Your data saved here
│   └── placement_dataset_training.csv
├── models/                         ← ML models (auto-created)
├── modules/                        ← All code modules
├── main.py                         ← RUN THIS 👈
├── train_models.py                 ← Run first time
├── setup.py                        ← Initial setup
├── requirements.txt
├── README.md                       ← Full documentation
└── SETUP_GUIDE.md                  ← Detailed guide
```

---

## 🎯 Quick Reference

### Score Calculations

**DSA Score** (from LeetCode API)
- Problems solved
- Difficulty distribution  
- Topic coverage
- Consistency

**Project Score** (from GitHub repos)
- Code complexity
- Architecture quality
- Tech stack depth
- Documentation

**Aptitude Score** (manual entry)
- https://aptitude-test.com/
- Range: 0-100

**ATS Score** (manual entry)
- https://enhancv.com/resources/resume-checker/
- Range: 0-100

**HR Score** (interview questions)
- Communication
- STAR structure
- Ownership
- Confidence

---

## 🧮 Prediction Formula

```
Final Probability = (ML Model Prediction) / (Company Difficulty)

Service Companies:
  Weight = 0.35×DSA + 0.35×Aptitude + 0.15×Projects + 0.15×CS

Product Companies:
  Weight = 0.45×DSA + 0.30×Projects + 0.15×CS + 0.10×Aptitude
```

---

## 🏢 Companies Covered

**Service**: TCS, Infosys, Wipro, Cognizant, HCL

**Product**: Amazon, Microsoft, Google, Meta, Apple, PayPal, Flipkart

---

## ✅ Checklist Before Running

- [ ] Python 3.7+ installed
- [ ] Internet connection available
- [ ] `pip install -r requirements.txt` completed
- [ ] `python train_models.py` run (first time only)
- [ ] Have LeetCode username ready (optional)
- [ ] Have GitHub repos ready (optional)

---

## 🆘 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run: `pip install -r requirements.txt` |
| LeetCode error | Check username, allow manual entry |
| GitHub clone failed | Ensure repo is public |
| Model not found | Run: `python train_models.py` |
| CSV error | Delete and recreate: `data/student_profiles.csv` |

---

## 💡 Pro Tips

1. **Accurate Data**: System quality depends on honest inputs
2. **Complete HR Round**: Spend time on answers (5-8 sentences each)
3. **Good Resume**: Focus on high ATS score
4. **Regular Updates**: Retake scores as you improve
5. **Backup Data**: Download `student_profiles.csv` regularly

---

## 📊 Example Run

```
$ python main.py

============================================================
⭐ PLACEMENT AI PREDICTION SYSTEM ⭐
============================================================

Enter Student ID: 101

[Profile not found, creating new...]

📝 BASIC INFORMATION
============================================================
Enter your CGPA (0-10): 3.5
Enter CS Fundamentals Score (0-100): 75
Enter number of Hackathon Wins (0-5): 2

1️⃣  DSA SCORE (From LeetCode)
============================================================
Enter your LeetCode username: john_doe

[Fetching LeetCode data...]
✅ DSA Score: 72/100

2️⃣  PROJECT SCORE (From GitHub)
============================================================
How many GitHub repositories do you want to analyze? 2

Enter GitHub repository URL 1: https://github.com/john/project1
Enter GitHub repository URL 2: https://github.com/john/project2

[Analyzing repositories...]
✅ Average Project Score: 68/100

3️⃣  APTITUDE SCORE
============================================================
Enter your Aptitude Score (0-100): 70

4️⃣  RESUME ATS SCORE
============================================================
Enter your Resume ATS Score (0-100): 72

🎤 HR ROUND INTERVIEW
============================================================
[5 questions with your answers...]
✅ HR Score: 75/100

🔮 GENERATING PREDICTIONS
[Loading/training models...]

============================================================
📈 PLACEMENT PREDICTION RESULTS
============================================================

👤 Student ID: 101
🎯 Overall Placement Probability: 68.45%

💼 Company Type Probabilities:
   Service-Based Companies: 72.30%
   Product-Based Companies: 65.80%

💰 Expected Salary:
   Predicted: ₹58.50 LPA
   Range: ₹46.80 - ₹70.20 LPA

🧑‍💼 Predicted Job Role: Software Engineer

🏆 Top Recommended Companies:
   1. TCS - 72.30%
   2. Infosys - 69.50%
   3. Wipro - 68.20%
   4. Amazon - 65.80%
   5. PayPal - 62.50%

📊 Company-Wise Placement Probabilities:
   TCS: 72.30%
   Infosys: 69.50%
   Wipro: 68.20%
   Amazon: 65.80%
   PayPal: 62.50%
   [... 5 more ...]

============================================================

✅ All operations completed successfully!
📁 Data saved to: data/student_profiles.csv
```

---

## 📈 Next Steps

1. **Run `python main.py`** to make your first prediction
2. **Review results** and verify they make sense
3. **Retake scores** if you want to improve predictions
4. **Export CSV** to share results (data/student_profiles.csv)
5. **Update company list** if needed (modules/company_logic.py)

---

## 📚 Full Documentation

For more details, see:
- **README.md** - Full project overview
- **SETUP_GUIDE.md** - Comprehensive setup guide
- **Module docstrings** - Individual module documentation

---

## 🎓 Key Learnings

The system teaches you:
- ✅ How ML predicts outcomes
- ✅ What companies really look for
- ✅ How scores are calculated
- ✅ Which skills matter most
- ✅ Company-specific hiring patterns

---

## 🚀 Ready to Start?

```bash
python main.py
```

That's it! 🎉

---

**Questions?** Check README.md or SETUP_GUIDE.md

**Problems?** Review error messages and troubleshooting section

**Feedback?** Results saved in data/student_profiles.csv

Happy Predicting! 🌟
