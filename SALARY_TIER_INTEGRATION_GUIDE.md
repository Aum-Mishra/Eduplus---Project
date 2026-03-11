# **SALARY TIER PROBABILITY MODULE - INTEGRATION GUIDE**

**Date:** March 5, 2026  
**Module:** `modules/salary_probability.py`  
**Status:** ✅ Independent, Non-Breaking, Production-Ready

---

## **OVERVIEW**

The **Salary Tier Probability Module** is a new, **completely independent** addition to the EduPlus placement prediction system.

### **Key Features:**

✅ **Non-Breaking:** Does NOT modify any existing code  
✅ **Independent:** Works as a separate parallel prediction pipeline  
✅ **Modular:** Can be added or removed without affecting placement predictions  
✅ **Reusable:** Uses same features and scalers as placement model  
✅ **Smart:** Multi-class XGBoost predicts 7 salary tiers  
✅ **Backward Compatible:** Existing system continues working unchanged  

---

## **MODULE ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────┐
│           EduPlus Placement System (EXISTING)            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Student Input Data                                      │
│         ↓                                                │
│  Feature Engineering (StandardScaler)                    │
│         ↓                                                │
│  ┌────────────────────────┬──────────────────────────┐  │
│  │                        │                          │  │
│  ↓                        ↓                          ↓  │
│  Placement Probability   Service/Product Prob.   Salary Tiers (NEW)
│  XGBoost Binary          (Skill-Based Logic)     XGBoost 7-Class
│  (Existing)              (Existing)              (New Module)
│  │                       │                        │   │
│  ↓                       ↓                        ↓   ↓
│  68% Placement      70%/69% Service/Product  42% 5-10 LPA
│                                              24% 10-15 LPA
│                                              12% 15-20 LPA
│                                              etc.
└─────────────────────────────────────────────────────────┘
```

---

## **CLASS STRUCTURE**

### **SalaryTierPredictor Class**

```python
class SalaryTierPredictor:
    
    SALARY_TIERS = {
        0: "0-5 LPA",
        1: "5-10 LPA",
        2: "10-15 LPA",
        3: "15-20 LPA",
        4: "20-30 LPA",
        5: "30-40 LPA",
        6: ">40 LPA"
    }
    
    # Methods:
    salary_to_tier(salary)                    # Convert salary to tier
    tier_to_salary_range(tier)                # Convert tier to label
    train_salary_model(df, features, scaler)  # Train the model
    predict_salary_distribution(student_scores)  # Predict for student
    format_salary_output(probabilities)       # Format output
    save_model()                              # Save to disk
    load_model()                              # Load from disk
    print_salary_distribution(probabilities)  # Pretty print
```

---

## **SALARY TIER DEFINITIONS**

```
Tier 0 → 0–5 LPA      (Entry level / No placement)
Tier 1 → 5–10 LPA     (Junior level)
Tier 2 → 10–15 LPA    (Associate level)
Tier 3 → 15–20 LPA    (Senior Associate level)
Tier 4 → 20–30 LPA    (Senior Developer level)
Tier 5 → 30–40 LPA    (Lead/Manager level)
Tier 6 → >40 LPA      (Senior Manager/Architect)
```

---

## **HOW TO USE IT**

### **1. INITIALIZATION & TRAINING**

```python
from modules.salary_probability import SalaryTierPredictor
import pandas as pd

# Create predictor instance
salary_predictor = SalaryTierPredictor()

# Load your dataset
df = pd.read_csv('data/student_profiles_100.csv')

# Define features (SAME as placement model)
feature_names = [
    "cgpa", "project_score", "dsa_score", "hackathon_wins",
    "aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"
]

# Train the model
# Option 1: Create new scaler
success = salary_predictor.train_salary_model(df, feature_names)

# Option 2: Reuse existing scaler from placement model (RECOMMENDED)
from modules.ml_models import MLModels
ml_models = MLModels()
ml_models.load_models()
success = salary_predictor.train_salary_model(
    df, 
    feature_names, 
    scaler=ml_models.scaler  # Reuse scaler
)

# Save the model
salary_predictor.save_model()
```

### **2. PREDICTION FOR A STUDENT**

```python
# Student data (from your CSV or user input)
student_data = {
    'cgpa': 7.5,
    'dsa_score': 75,
    'project_score': 68,
    'cs_fundamentals_score': 72,
    'aptitude_score': 80,
    'hr_score': 85,
    'resume_ats_score': 78,
    'hackathon_wins': 2
}

# Predict salary distribution
salary_dist = salary_predictor.predict_salary_distribution(student_data)

# Display results
salary_predictor.print_salary_distribution(salary_dist)

# Access specific probabilities
print(f"Chance of 5-10 LPA: {salary_dist['5-10 LPA']}%")
print(f"Chance of >20 LPA: {salary_dist['20-30 LPA'] + salary_dist['30-40 LPA'] + salary_dist['>40 LPA']}%")
```

### **3. LOAD PRE-TRAINED MODEL**

```python
# Create instance
salary_predictor = SalaryTierPredictor()

# Load existing model
if salary_predictor.load_model():
    # Model loaded, ready to predict
    salary_dist = salary_predictor.predict_salary_distribution(student_data)
else:
    # Model doesn't exist, train it
    salary_predictor.train_salary_model(df, feature_names, scaler=ml_models.scaler)
    salary_predictor.save_model()
```

---

## **INTEGRATION WITH MAIN.PY**

### **OPTION 1: Add to calculate_placement_probabilities() function**

```python
# In main.py, after calculating service/product probabilities

def calculate_placement_probabilities(student_data):
    """Calculate placement, service/product, AND salary probabilities"""
    
    # ... existing code for placement probabilities ...
    
    # NEW: Calculate salary tier probabilities
    print("\n[STEP 4] Predicting salary tier distribution...")
    try:
        salary_predictor = SalaryTierPredictor()
        
        # Try to load existing model
        if salary_predictor.load_model():
            print("[OK] Salary model loaded successfully!")
        else:
            print("[!] Salary model not found. Training new model...")
            from train_models import train_all_models
            # Assume train_all_models() also trains salary model
            train_all_models()
            if not salary_predictor.load_model():
                raise Exception("Failed to train salary model")
            print("[OK] Salary model trained and loaded!")
        
        # Predict salary distribution
        salary_dist = salary_predictor.predict_salary_distribution(student_data)
        print(f"[OK] Salary distribution predicted!")
        
    except Exception as e:
        print(f"[ERROR] Error predicting salary: {e}")
        salary_dist = None
    
    return {
        'overall_placement_probability': ml_placement_prob * 100,
        'service_company_probability': service_prob,
        'product_company_probability': product_prob,
        'salary_distribution': salary_dist,  # NEW
        'salary_prediction': salary_pred,
        'job_role_prediction': role_name,
        'recommended_companies': recommended_companies
    }
```

### **OPTION 2: Separate Salary Prediction Function**

```python
def predict_student_salary(student_data, feature_names):
    """Predict salary distribution for a student"""
    
    from modules.salary_probability import SalaryTierPredictor
    
    salary_predictor = SalaryTierPredictor()
    
    # Load or train model
    if not salary_predictor.load_model():
        df = pd.read_csv(STUDENT_CSV)
        from modules.ml_models import MLModels
        ml_models = MLModels()
        ml_models.load_models()
        salary_predictor.train_salary_model(df, feature_names, scaler=ml_models.scaler)
        salary_predictor.save_model()
    
    # Predict
    salary_dist = salary_predictor.predict_salary_distribution(student_data)
    return salary_dist
```

---

## **OUTPUT EXAMPLES**

### **Example 1: Excellent Student**

```
============================================================
💰 SALARY TIER PROBABILITY DISTRIBUTION
============================================================
0-5 LPA      →   1.2% █
5-10 LPA     →   8.3% ██
10-15 LPA    →  22.5% █████
15-20 LPA    →  24.8% ██████
20-30 LPA    →  26.4% ██████
30-40 LPA    →  12.2% ███
>40 LPA      →   4.6% █

============================================================
📊 SALARY THRESHOLDS:
   Probability of salary > 15 LPA: 68.0%
   Probability of salary > 20 LPA: 43.2%
   Probability of salary > 40 LPA: 4.6%

🎯 MOST LIKELY SALARY RANGE:
   20-30 LPA with 26.4% probability
============================================================
```

### **Example 2: Average Student**

```
============================================================
💰 SALARY TIER PROBABILITY DISTRIBUTION
============================================================
0-5 LPA      →   3.5% █
5-10 LPA     →  34.2% ████████
10-15 LPA    →  35.8% █████████
15-20 LPA    →  18.2% ████
20-30 LPA    →   6.8% █
30-40 LPA    →   1.2% 
>40 LPA      →   0.3% 

============================================================
📊 SALARY THRESHOLDS:
   Probability of salary > 15 LPA: 26.3%
   Probability of salary > 20 LPA: 8.3%
   Probability of salary > 40 LPA: 0.3%

🎯 MOST LIKELY SALARY RANGE:
   10-15 LPA with 35.8% probability
============================================================
```

### **Example 3: Struggling Student**

```
============================================================
💰 SALARY TIER PROBABILITY DISTRIBUTION
============================================================
0-5 LPA      →  42.5% ██████████
5-10 LPA     →  38.2% █████████
10-15 LPA    →  14.8% ███
15-20 LPA    →   3.5% █
20-30 LPA    →   0.7% 
30-40 LPA    →   0.2% 
>40 LPA      →   0.1% 

============================================================
📊 SALARY THRESHOLDS:
   Probability of salary > 15 LPA: 4.5%
   Probability of salary > 20 LPA: 1.0%
   Probability of salary > 40 LPA: 0.1%

🎯 MOST LIKELY SALARY RANGE:
   0-5 LPA with 42.5% probability
============================================================
```

---

## **KEY DIFFERENCES FROM PLACEMENT MODEL**

| Aspect | Placement Model | Salary Model |
|--------|-----------------|--------------|
| **Type** | Binary Classification | Multi-Class Classification |
| **Output** | Single probability (0-1) | 7 probabilities (sum to 1) |
| **Purpose** | "Will student be placed?" | "What salary tier?" |
| **Classes** | 2 classes (Placed/Not Placed) | 7 classes (tiers 0-6) |
| **Target Variable** | "Placed"/"Not Placed" | Salary LPA value (→ tier) |
| **Modification** | NONE - Unchanged | NEW - Added parallel |

---

## **DATA REQUIREMENTS**

The module needs:

1. **Training Dataset** with columns:
   ```
   - cgpa
   - dsa_score
   - project_score
   - cs_fundamentals_score
   - aptitude_score
   - hr_score
   - resume_ats_score
   - hackathon_wins
   - salary_lpa (or expected_salary)
   - placement_status (to identify placed students)
   ```

2. **Feature Names** (in order):
   ```python
   ["cgpa", "project_score", "dsa_score", "hackathon_wins",
    "aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"]
   ```

3. **StandardScaler** (reused from placement model for consistency)

---

## **MODEL CONFIGURATION**

```python
XGBClassifier(
    objective="multi:softprob",    # Multi-class softmax
    num_class=7,                   # 7 salary tiers
    n_estimators=200,              # 200 trees
    max_depth=4,                   # Shallow trees (prevent overfitting)
    learning_rate=0.05,            # Conservative learning
    subsample=0.7,                 # 70% sample per tree
    colsample_bytree=0.7,          # 70% features per tree
    random_state=42,               # Reproducibility
    eval_metric='mlogloss'         # Multi-class loss metric
)
```

**Why this configuration?**

- **Shallow trees (max_depth=4):** Prevents overfitting on relatively small dataset
- **Conservative learning (0.05):** Better generalization
- **subsample=0.7:** Reduces variance
- **200 trees:** Sufficient for stable predictions
- **multi:softprob:** Proper multi-class probability output

---

## **FILES CREATED**

```
modules/
├── salary_probability.py          ← NEW MODULE
├── ml_models.py                   (UNCHANGED)
├── feature_engineering.py         (UNCHANGED)
├── service_product_probability.py (UNCHANGED)
└── ... (other existing modules)

models/
├── placement_model.pkl            (EXISTING)
├── salary_tier_model.pkl          ← NEW MODEL
├── salary_tier_scaler.pkl         ← NEW SCALER
└── ... (other existing models)
```

---

## **BACKWARD COMPATIBILITY**

✅ **NO existing files modified**  
✅ **NO changes to main.py required** (optional integration)  
✅ **NO changes to ML models**  
✅ **NO changes to feature engineering**  
✅ **NO changes to service/product logic**  

The system works as-is. The salary module is a **pure addition** that can be:
- Activated by importing it
- Used on-demand
- Removed without breaking anything
- Trained independently

---

## **ERROR HANDLING**

The module handles:

1. **Missing Data:** Returns None for invalid inputs
2. **Model Not Trained:** Checks `is_trained` flag
3. **Missing Salary Column:** Looks for both `salary_lpa` and `expected_salary`
4. **Insufficient Data:** Requires minimum 10 placed students
5. **File I/O Errors:** Handles pickle load/save gracefully

---

## **SAMPLE WORKFLOW**

```
PHASE 1: TRAINING (One-time)
├── Load dataset with 4000 students
├── Filter placed students
├── Convert salary to tier labels
├── Scale features (reuse from placement model)
└── Train XGBoost 7-class classifier
    └── Save model + scaler to pickle

PHASE 2: PREDICTION (Per student)
├── Load pre-trained model
├── Receive student feature dictionary
├── Scale student features
├── Get probability for each tier
├── Format output (7 probabilities)
└── Return salary distribution

PHASE 3: PRESENTATION
├── Display tier-wise probabilities
├── Calculate composite probabilities
  │   └── "Chance of >20 LPA" = P(tier4) + P(tier5) + P(tier6)
├── Identify most likely salary range
└── Show bar chart visualization
```

---

## **TESTING THE MODULE**

Create a simple test script:

```python
from modules.salary_probability import SalaryTierPredictor
import pandas as pd

# Test 1: Salary to Tier Conversion
print("TEST 1: Salary to Tier Conversion")
print(f"Salary 4 LPA → Tier {SalaryTierPredictor.salary_to_tier(4)}")   # 0
print(f"Salary 8 LPA → Tier {SalaryTierPredictor.salary_to_tier(8)}")   # 1
print(f"Salary 12 LPA → Tier {SalaryTierPredictor.salary_to_tier(12)}")  # 2
print(f"Salary 50 LPA → Tier {SalaryTierPredictor.salary_to_tier(50)}")  # 6

# Test 2: Training
print("\nTEST 2: Model Training")
df = pd.read_csv('data/student_profiles_100.csv')
feature_names = ["cgpa", "project_score", "dsa_score", "hackathon_wins",
                 "aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"]
predictor = SalaryTierPredictor()
success = predictor.train_salary_model(df, feature_names)
print(f"Training successful: {success}")

# Test 3: Prediction
print("\nTEST 3: Sample Prediction")
student = {
    'cgpa': 7.5, 'dsa_score': 75, 'project_score': 68,
    'cs_fundamentals_score': 72, 'aptitude_score': 80,
    'hr_score': 85, 'resume_ats_score': 78, 'hackathon_wins': 2
}
dist = predictor.predict_salary_distribution(student)
predictor.print_salary_distribution(dist)

# Test 4: Save/Load
print("\nTEST 4: Save and Load")
predictor.save_model()
predictor2 = SalaryTierPredictor()
loaded = predictor2.load_model()
print(f"Model loaded: {loaded}")
```

---

## **ADVANTAGES OF THIS APPROACH**

1. **Modular:** Can be used independently
2. **Non-Breaking:** Doesn't modify existing code
3. **Realistic:** 7-tier classification reflects real salary ranges
4. **Actionable:** Answers specific salary questions
5. **Transparent:** Shows probability for each tier
6. **Smart:** Uses ML to learn actual salary patterns
7. **Efficient:** Reuses existing features and scalers
8. **Scalable:** Easy to add more tiers or modify ranges

---

## **FUTURE ENHANCEMENTS**

Possible improvements:

1. **Tier Probability Confidence:** Add confidence intervals
2. **Expected Salary Value:** Predict mean salary (regression)
3. **Company-Wise Salary:** Salary by company type
4. **Year-Over-Year Trends:** Historical salary comparisons
5. **Location-Based Salaries:** Regional salary variations
6. **Inter-Tier Analysis:** Why student likely each tier
7. **Salary Growth Path:** Projected salary over time

---

## **SUMMARY**

The **Salary Tier Probability Module** is a powerful, independent addition to EduPlus that:

✅ Provides **salary distribution predictions**  
✅ Answers **specific salary threshold questions**  
✅ Maintains **complete backward compatibility**  
✅ Uses **proven XGBoost multi-class approach**  
✅ Follows **existing system architecture**  
✅ Requires **NO changes to existing code**  

Students can now know not just **if they'll be placed**, but **how much they'll earn**! 💰

