# Configuration & Customization Guide

## 🎛️ System Configuration

This file explains how to customize the placement AI system for your needs.

---

## 1️⃣ Add or Modify Companies

**File**: `modules/company_logic.py`

### Current Company Database
```python
COMPANIES_DB = {
    "CompanyName": {
        "type": "Service" or "Product",
        "difficulty_factor": 0.9,  # 0.8-1.5 range
        "min_cgpa": 3.0,
        "weights": {
            "dsa_score": 0.35,
            "aptitude_score": 0.35,
            "project_score": 0.15,
            "cs_fundamentals_score": 0.15
        }
    }
}
```

### Add New Company

```python
# Example: Add Accenture (Service)
"Accenture": {
    "type": "Service",
    "difficulty_factor": 0.93,
    "min_cgpa": 3.0,
    "weights": {
        "dsa_score": 0.35,
        "aptitude_score": 0.35,
        "project_score": 0.15,
        "cs_fundamentals_score": 0.15
    }
}

# Example: Add Apple (Product)
"Apple": {
    "type": "Product",
    "difficulty_factor": 1.4,
    "min_cgpa": 3.6,
    "weights": {
        "dsa_score": 0.45,
        "project_score": 0.30,
        "cs_fundamentals_score": 0.15,
        "aptitude_score": 0.10
    }
}
```

### Difficulty Factor Guide
```
0.8-0.9   = Easy (HCL tier)
0.9-1.0   = Moderate (TCS/Infosys tier)
1.0-1.2   = Competitive (Flipkart/PayPal tier)
1.2-1.4   = Difficult (Amazon/Microsoft tier)
1.4+      = Very Difficult (Google tier)
```

---

## 2️⃣ Customize Weight Distributions

### Service Companies (Current)
```python
"Service": {
    "dsa_score": 0.35,           # DSA is important
    "aptitude_score": 0.35,      # Aptitude matters equally
    "project_score": 0.15,       # Projects less important
    "cs_fundamentals_score": 0.15
}
```

**To emphasize DSA more:**
```python
"Service": {
    "dsa_score": 0.45,
    "aptitude_score": 0.30,
    "project_score": 0.15,
    "cs_fundamentals_score": 0.10
}
```

### Product Companies (Current)
```python
"Product": {
    "dsa_score": 0.45,
    "project_score": 0.30,
    "cs_fundamentals_score": 0.15,
    "aptitude_score": 0.10
}
```

**To emphasize Projects more:**
```python
"Product": {
    "dsa_score": 0.40,
    "project_score": 0.40,
    "cs_fundamentals_score": 0.15,
    "aptitude_score": 0.05
}
```

---

## 3️⃣ Modify HR Interview Questions

**File**: `modules/hr_round.py`

### Current Questions
```python
QUESTIONS = [
    "Describe a project where you had a major responsibility...",
    "Tell me about a time when your team faced a problem...",
    "Describe a failure or mistake you made...",
    "How do you handle pressure or tight deadlines?",
    "Explain a situation where you had to learn something new..."
]
```

### Add Custom Questions
```python
QUESTIONS = [
    "Question 1 here?",
    "Question 2 here?",
    "Question 3 here?",
    "Question 4 here?",
    "Question 5 here?",
    "Question 6 here?",  # Add more if needed
]
```

### Example: Manager-Focused Interview
```python
QUESTIONS = [
    "Describe a time when you led a team or project.",
    "Tell me about a conflict you resolved in a team.",
    "How do you handle multiple projects with tight deadlines?",
    "Describe your approach to mentoring junior developers.",
    "What's your strategy for improving team productivity?"
]
```

---

## 4️⃣ Adjust HR Evaluation Weights

**File**: `modules/hr_round.py`, `final_hr_score()` function

### Current Weights
```python
def final_hr_score(comm, star, ownership, consistency):
    return round(
        0.25 * comm +           # 25% Communication
        0.25 * star +           # 25% STAR structure
        0.25 * ownership +      # 25% Ownership
        0.25 * consistency,     # 25% Consistency
        2
    )
```

### Make Communication More Important
```python
def final_hr_score(comm, star, ownership, consistency):
    return round(
        0.40 * comm +           # 40% Communication
        0.20 * star +           # 20% STAR structure
        0.20 * ownership +      # 20% Ownership
        0.20 * consistency,     # 20% Consistency
        2
    )
```

### HR Weight Customization Guide
```
Weights must sum to 1.0 (100%)

For Technical Roles:
  Communication: 0.20
  STAR: 0.25
  Ownership: 0.30
  Consistency: 0.25

For Management Roles:
  Communication: 0.35
  STAR: 0.30
  Ownership: 0.25
  Consistency: 0.10

For Startup Culture:
  Communication: 0.25
  STAR: 0.20
  Ownership: 0.35
  Consistency: 0.20
```

---

## 5️⃣ Modify Feature Engineering

**File**: `modules/feature_engineering.py`

### Add New Derived Features
```python
def create_derived_features(self, df):
    df = df.copy()
    
    # Existing features
    df["technical_score"] = (
        df["dsa_score"] + df["project_score"] + df["cs_fundamentals_score"]
    ) / 3
    
    df["soft_skill_score"] = (
        df["aptitude_score"] + df["hr_score"]
    ) / 2
    
    # Add new features
    df["overall_score"] = (
        0.4 * df["technical_score"] + 0.6 * df["soft_skill_score"]
    )
    
    df["aptitude_dsa_ratio"] = df["aptitude_score"] / (df["dsa_score"] + 1)
    
    return df
```

### Update Feature List
```python
BASE_FEATURES = [
    "cgpa", "project_score", "dsa_score", "hackathon_wins",
    "aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"
]

DERIVED_FEATURES = [
    "technical_score", 
    "soft_skill_score",
    "overall_score",          # NEW
    "aptitude_dsa_ratio"      # NEW
]
```

---

## 6️⃣ Adjust ML Model Parameters

**File**: `modules/ml_models.py`

### Placement Model XGBoost Parameters
```python
base_model = XGBClassifier(
    n_estimators=150,        # Number of boosting rounds
    max_depth=3,             # Tree depth (deeper = more complex)
    learning_rate=0.05,      # Step size (lower = slower learning)
    subsample=0.7,           # Row subsampling
    colsample_bytree=0.7,    # Column subsampling
    reg_lambda=1.5,          # L2 regularization
    reg_alpha=0.5,           # L1 regularization
    random_state=42
)
```

### Tune for Better Accuracy
```python
# For more complex patterns:
base_model = XGBClassifier(
    n_estimators=200,        # More boosting
    max_depth=5,             # Deeper trees
    learning_rate=0.03,      # Slower learning
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,          # Less regularization
    reg_alpha=0.3,
    random_state=42
)
```

### Tune for Generalization
```python
# To prevent overfitting:
base_model = XGBClassifier(
    n_estimators=100,        # Fewer boosting
    max_depth=2,             # Shallower trees
    learning_rate=0.1,       # Faster learning
    subsample=0.6,           # More subsampling
    colsample_bytree=0.6,
    reg_lambda=2.0,          # More regularization
    reg_alpha=1.0,
    random_state=42
)
```

---

## 7️⃣ Customize Probability Calibration

**File**: `modules/prediction.py`

### Current Calibration
```python
def realistic_probability(self, raw_prob, student):
    skill_avg = np.mean([...])
    soft_avg = np.mean([...])
    ats = student["resume_ats_score"]
    cgpa = student["cgpa"]

    p = raw_prob
    
    # Penalties
    if skill_avg < 40: p *= 0.4
    if ats < 35: p *= 0.5
    if soft_avg < 40: p *= 0.6
    if cgpa < 6: p *= 0.5
    
    # Smoothing
    p = 0.15 + 0.7 * p
    
    return round(p*100, 2)
```

### Stricter Calibration (Less 50-50)
```python
def realistic_probability(self, raw_prob, student):
    # ... same setup ...
    
    # Stricter penalties
    if skill_avg < 30: p *= 0.2
    if ats < 25: p *= 0.3
    if soft_avg < 30: p *= 0.3
    if cgpa < 5.5: p *= 0.4
    
    # Stronger smoothing
    p = 0.05 + 0.9 * p
    
    return round(p*100, 2)
```

### Lenient Calibration
```python
def realistic_probability(self, raw_prob, student):
    # ... same setup ...
    
    # Lenient penalties
    if skill_avg < 50: p *= 0.8
    if ats < 45: p *= 0.9
    if soft_avg < 50: p *= 0.85
    if cgpa < 7: p *= 0.95
    
    # Gentle smoothing
    p = 0.25 + 0.5 * p
    
    return round(p*100, 2)
```

---

## 8️⃣ Modify Training Data

**File**: `train_models.py`

### Use Custom Training Dataset
```python
def load_training_data():
    # Instead of sample data, load your own
    df = pd.read_csv('data/your_custom_dataset.csv')
    
    # Ensure your CSV has these columns:
    # cgpa, dsa_score, project_score, aptitude_score, hr_score,
    # resume_ats_score, cs_fundamentals_score, hackathon_wins,
    # placement_status, salary_lpa, job_role, company_name
    
    return df
```

### Increase Training Data Quality
```python
def load_training_data():
    df = pd.read_csv('data/placement_dataset_training.csv')
    
    # Remove invalid records
    df = df[df['cgpa'] > 0]
    df = df[df['dsa_score'] >= 0]
    df = df[df['dsa_score'] <= 100]
    
    # Remove outliers
    df = df[df['salary_lpa'] < 200]  # Remove outliers
    
    return df
```

---

## 9️⃣ Adjust Difficulty Factors

**File**: `modules/company_logic.py`

### Current Difficulty Distribution
```
Easy (0.8-0.9):   HCL, TCS
Moderate (0.9-1.0): Cognizant, Wipro, Infosys
Competitive (1.0-1.2): Flipkart, PayPal
Hard (1.2-1.4):   Amazon, Microsoft, Meta, Apple
Harder (1.4+):    Google
```

### Adjust Based on Your Data
```python
# If you find TCS is actually harder:
"TCS": {
    "type": "Service",
    "difficulty_factor": 1.05,  # Instead of 0.90
    # ...
}

# If Amazon is easier than expected:
"Amazon": {
    "type": "Product",
    "difficulty_factor": 1.10,  # Instead of 1.20
    # ...
}
```

---

## 🔟 LeetCode API Configuration

**File**: `modules/leetcode_dsa.py`

### No configuration needed! But you can modify:

```python
# Increase timeout if LeetCode is slow
res = requests.post(url, json=payload, timeout=15)  # Was 10

# Adjust DSA score weights if needed
dsa_score = (
    0.50 * pss +  # Increased from 0.40
    0.20 * tms +  # Decreased from 0.25
    0.20 * cs +
    contest_weight * cps
)
```

---

## 1️⃣1️⃣ GitHub Analysis Configuration

**File**: `modules/github_project.py`

### Adjust Code Extension Tracking
```python
CODE_EXT = [".py", ".js", ".ts", ".java", ".cpp", ".c"]
# Add more: ".go", ".rust", ".php", etc.
```

### Modify Technology Keywords
```python
TECH_KEYWORDS = {
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    # Add more technologies
    "NextJS": ["next", "nextjs"],
    "Docker": ["docker", "dockerfile"],
    "Kubernetes": ["kubernetes", "k8s"],
}
```

### Adjust Score Thresholds
```python
# In logic_density function
score = min((functions * 2 + control_flow) / 50, 5)  # Adjust denominator

# In scope_score function
if loc > 3000: return 5  # Increase thresholds if needed
```

---

## 1️⃣2️⃣ Combination & Override Weights

**File**: `modules/prediction.py`

### Adjust ML + Company Weight Balance
```python
# Current: 60% ML, 40% Company
alpha = 0.6
combined_prob = alpha * base_prob + (1 - alpha) * company_score

# Make ML more important (70%):
alpha = 0.7

# Make Company logic more important (30%):
alpha = 0.5
```

---

## 📋 Configuration Checklist

Before customizing, verify:

- [ ] Backup original files
- [ ] Test changes locally first
- [ ] Retrain models after changes
- [ ] Validate predictions on known cases
- [ ] Update documentation
- [ ] Test with sample data

---

## 🔄 Configuration Examples

### Example 1: Startup-Focused System
```python
# Less emphasis on CGPA, more on projects
"Startup Company": {
    "type": "Product",
    "difficulty_factor": 0.95,  # Easy for startups
    "min_cgpa": 2.8,            # Lower CGPA requirement
    "weights": {
        "dsa_score": 0.25,      # Less important
        "project_score": 0.50,  # Very important
        "cs_fundamentals_score": 0.15,
        "aptitude_score": 0.10
    }
}

# HR focused on passion and learning
QUESTIONS = [
    "What excites you about tech?",
    "Describe a project you built for fun",
    "How do you stay updated with tech?",
    "Tell about learning from failure",
    "Why do you want to join startups?"
]
```

### Example 2: FAANG-Focused System
```python
# High emphasis on algorithms and competition
"Google": {
    "difficulty_factor": 1.5,  # Very difficult
    "min_cgpa": 3.7,
    "weights": {
        "dsa_score": 0.60,      # Very high
        "project_score": 0.20,
        "cs_fundamentals_score": 0.20,
        "aptitude_score": 0.00  # Not important
    }
}

# Weights for ML models
weights = {
    "dsa_score": 0.50,
    "project_score": 0.25,
    "cs_fundamentals_score": 0.25,
    "aptitude_score": 0.00
}
```

### Example 3: Startup+Service Mix
```python
# For companies that value both technical and soft skills
"Hybrid Company": {
    "type": "Service",
    "difficulty_factor": 1.05,
    "min_cgpa": 3.2,
    "weights": {
        "dsa_score": 0.30,
        "aptitude_score": 0.25,
        "project_score": 0.25,
        "cs_fundamentals_score": 0.20
    }
}
```

---

## 🚀 After Configuration

1. **Retrain Models**
   ```bash
   python train_models.py
   ```

2. **Test with Sample Student**
   ```bash
   python main.py
   ```

3. **Verify Results**
   - Check if predictions make sense
   - Verify company probabilities align with difficulty
   - Ensure no extreme values (0% or 100%)

4. **Update Documentation**
   - Document your changes
   - Note difficulty factors used
   - Record custom questions

---

## ⚠️ Important Notes

- **Always backup** before making changes
- **Test thoroughly** before deployment
- **Retrain models** after modifying weights or features
- **Validate results** with known cases
- **Document changes** for future reference
- **Keep original** copy as fallback

---

**Last Updated**: January 2026  
**Configuration Version**: 1.0  
**Status**: Ready for Customization ✅
