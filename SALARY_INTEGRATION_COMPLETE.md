# Salary Tier Prediction Integration - Complete Guide

## Overview

The salary tier prediction model has been **successfully integrated** into the main placement prediction pipeline. The system now provides:

1. **Overall Placement Probability** (5% - 100%)
2. **Service/Product Company Probabilities**
3. **Salary Prediction (Single Value)** - XGBRegressor
4. **Salary Tier Distribution** - NEW! - XGBClassifier (7-class multi-classification)

---

## Architecture & Integration

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                  PLACEMENT PREDICTION PIPELINE               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Student Data Input                                       │
│     └─► Feature Engineering (8 + 2 derived features)        │
│                                                               │
│  2. Placement Probability Calculation                        │
│     └─► ML Model → Penalties → Smoothing (5%-100%)          │
│                                                               │
│  3. Service/Product Company Classification                   │
│     └─► Skill-based weighting (Domain Logic)                │
│                                                               │
│  4. Salary Prediction                                        │
│     ├─► Single Value: XGBRegressor (47 LPA avg)            │
│     │                                                         │
│     └─► Tier Distribution: XGBClassifier (7-tier)          │
│         ├─ 0-5 LPA     (Low)                              │
│         ├─ 5-10 LPA    (Mid-Low)                          │
│         ├─ 10-15 LPA   (Mid)                              │
│         ├─ 15-20 LPA   (Mid-High)                         │
│         ├─ 20-30 LPA   (High)                             │
│         ├─ 30-40 LPA   (Very High)                        │
│         └─ >40 LPA     (Elite)                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Model Training & Files

**Training Script:** [train_salary_model.py](train_salary_model.py)

**Trained Model Files** (in `models/` directory):
- `salary_tier_model.pkl` - XGBoost multi-class classifier
- `salary_tier_scaler.pkl` - StandardScaler for feature normalization
- `salary_tier_features.pkl` - List of feature names

**Training Data** (4000 students):
- Source: `data/campus_placement_dataset_final_academic_4000.csv`
- Placed Students: 2000
- Salary Tier Distribution:
  - 0-5 LPA: 518 (25.9%)
  - 5-10 LPA: 1229 (61.5%)
  - 10-15 LPA: 20 (1.0%)
  - 15-20 LPA: 14 (0.7%)
  - 20-30 LPA: 72 (3.6%)
  - 30-40 LPA: 84 (4.2%)
  - >40 LPA: 63 (3.1%)

---

## Code Integration Points

### 1. Import Statement
**File:** [main.py](main.py#L21)
```python
from modules.salary_probability import SalaryTierPredictor
```

### 2. Training the Model
**Command:**
```bash
python train_salary_model.py
```

This trains the salary tier model on 2000 placed students from the 4000-student dataset and saves it to disk.

### 3. Prediction Integration in main.py
**Function:** `calculate_placement_probabilities()` (Lines 310-440)

**New Code Section (STEP 4B):**
```python
# STEP 4B: Get salary tier distribution
print("\n[STEP 4B] Predicting salary tier distribution...")
try:
    salary_predictor = SalaryTierPredictor()
    if salary_predictor.load_model():
        # Predict salary tier distribution
        salary_distribution = salary_predictor.predict_salary_distribution(student_data)
        # ... display results ...
    else:
        print("[!] Salary tier model not found. Train it using: python train_salary_model.py")
except Exception as e:
    print(f"[!] Error with salary tier prediction: {e}")
```

**Return Dictionary** (now includes salary_distribution):
```python
return {
    'overall_placement_probability': ml_placement_prob * 100,
    'service_company_probability': service_prob,
    'product_company_probability': product_prob,
    'salary_prediction': salary_pred,
    'salary_distribution': salary_distribution,  # NEW!
    'job_role_prediction': role_name,
    'recommended_companies': recommended_companies
}
```

### 4. Display Integration in main.py
**Function:** `display_results()` (Lines 442-490)

**New Display Section:**
```python
# Salary tier distribution
if probabilities.get('salary_distribution'):
    print("\n[SALARY TIER DISTRIBUTION]")
    salary_dist = probabilities['salary_distribution']
    
    # Display each tier with probability and bar chart
    for tier, prob in sorted_tiers:
        bar = "█" * int(prob / 5)
        print(f"  {tier:12} → {prob:6.1f}% {bar}")
    
    # Show composite probabilities
    print(f"\n  Chance of >15 LPA: {above_15_lpa:.1f}%")
    print(f"  Chance of >20 LPA: {above_20_lpa:.1f}%")
    print(f"  Chance of >40 LPA: {above_40_lpa:.1f}%")
```

---

## Module Implementation

### SalaryTierPredictor Class
**File:** [modules/salary_probability.py](modules/salary_probability.py)

**Key Methods:**

1. **`train_salary_model(df, feature_names, scaler=None)`**
   - Trains XGBoost multi-class classifier on placed students
   - Converts salaries to tiers (0-6)
   - Uses existing scaler from placement model
   - Saves: model, scaler, feature names

2. **`predict_salary_distribution(student_scores)`**
   - Predicts probability for each salary tier
   - Creates derived features automatically
   - Returns dict: {"0-5 LPA": 2.1, "5-10 LPA": 15.3, ...}

3. **`load_model()`**
   - Loads pre-trained model from disk
   - Restores scaler and feature names
   - Returns: True if successful

4. **`save_model()`**
   - Saves model, scaler, and features to `models/` directory

5. **`format_salary_output(probabilities)`**
   - Converts raw probabilities (0-1) to percentages (0-100%)
   - Formats as tier labels with percentages

---

## Feature Engineering

### Base Features (8)
```python
"cgpa", "project_score", "dsa_score", "hackathon_wins",
"aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"
```

### Derived Features (2) - Calculated Automatically
```python
technical_score = (dsa_score + project_score + cs_fundamentals_score) / 3
soft_skill_score = (aptitude_score + hr_score) / 2
```

### Normalization
- Uses StandardScaler
- Same scaler as placement model
- Applied to all 10 features during prediction

---

## Example Workflow

### Input
```python
student_data = {
    'student_id': 200005,
    'cgpa': 8.2,
    'dsa_score': 85.3,
    'project_score': 82.5,
    'cs_fundamentals_score': 74.2,
    'aptitude_score': 78.5,
    'hr_score': 81.2,
    'resume_ats_score': 76.8,
    'hackathon_wins': 1
}
```

### Processing Steps

1. **Feature Engineering**
   - Base features extracted: 8 values
   - Derived features created: 2 values
   - Total: 10 features

2. **Feature Scaling**
   - Each feature normalized using StandardScaler

3. **Model Prediction**
   - XGBoost predicts probability for each of 7 salary tiers
   - Output: [0.01, 0.006, 0.009, 0.003, 0.129, 0.194, 0.65]

4. **Formatting**
   - Convert to percentages and tier labels
   - Sort by probability (highest first)

### Output
```
💰 SALARY TIER PROBABILITY DISTRIBUTION:
--------------------------------------------------
  >40 LPA      →   65.0% █████████████
  30-40 LPA    →   19.4% ███
  20-30 LPA    →   12.9% ██
  0-5 LPA      →    1.0%
  10-15 LPA    →    0.9%
  5-10 LPA     →    0.6%
  15-20 LPA    →    0.3%
--------------------------------------------------

📊 SALARY THRESHOLDS:
  • Probability of earning >15 LPA: 97.6%
  • Probability of earning >20 LPA: 97.3%
  • Probability of earning >40 LPA: 65.0%

🎯 MOST LIKELY SALARY RANGE:
   >40 LPA with 65.0% probability
```

---

## Model Training & Deployment

### Step 1: Train the Model
```bash
# Train salary tier model on 4000-student dataset
python train_salary_model.py
```

**Output Files Created:**
- `models/salary_tier_model.pkl` (XGBoost model)
- `models/salary_tier_scaler.pkl` (StandardScaler)
- `models/salary_tier_features.pkl` (Feature names)

### Step 2: Run Predictions
```bash
# Run interactive placement prediction system
python main.py

# Or run integration example
python integration_example.py
```

---

## Key Design Decisions

### 1. Independent Multi-Classification Approach
- **Why?** Provides probability distribution, not just a single value
- **Benefit:** More informative - shows likelihood of each salary range
- **Complement:** Works alongside XGBRegressor for single salary prediction

### 2. 7 Salary Tiers
- **Why?** Captures market reality: most students earn 5-10 LPA, some earn 40+ LPA
- **Balanced:** Tiers capture natural "salary bands" in market
- **Useful:** Easier to interpret than exact LPA value

### 3. Feature Reuse
- **Why?** Same 10 features as placement model
- **Benefit:** Consistency, efficiency, reduced overfitting
- **Implementation:** Same StandardScaler used for both models

### 4. Automatic Feature Creation
- **Why?** Feature engineering is transparent to user
- **Benefit:** Users pass raw student data, system handles transformations
- **Safety:** Features are created in prediction method as well as training

### 5. XGBoost Multi-Class
- **Why?** Proven effective for salary prediction
- **Hyperparameters:**
  - n_estimators=200
  - max_depth=4
  - learning_rate=0.05
  - subsample=0.7
  - colsample_bytree=0.7

---

## Performance Metrics

### Training Results (2000 placed students)
```
Model Configuration:
  • Algorithm: XGBoost Multi-Class Classifier
  • Classes: 7 (salary tiers)
  • Training Samples: 2000
  • Features: 10 (8 base + 2 derived)
  
Training Completed:
  ✅ Model trained successfully
  ✅ Feature names saved
  ✅ Scaler saved for consistency
```

### Prediction Example
**For high-performing student (dsa_score=85.3, project=82.5, cgpa=8.2):**
- Placement Probability: 100.00%
- Service Companies: 92.33%
- Product Companies: 92.85%
- Predicted Salary (Regression): 46.01 LPA
- Most Likely Tier: >40 LPA (65.0% probability)

---

## Error Handling & Robustness

### Graceful Degradation
```
If salary tier model not found:
  ✅ System continues with single salary prediction
  ⚠️  Shows warning: "Training model not found"
  ℹ️  Provides instruction: "Run: python train_salary_model.py"
```

### Automatic Feature Creation
```
If derived features missing from input:
  ✅ System automatically creates them
  ℹ️  technical_score = (dsa + project + cs) / 3
  ℹ️  soft_skill_score = (aptitude + hr) / 2
```

### Feature Validation
```
If required features missing:
  ✅ Clear error message with list of required features
  ℹ️  Shows which features are missing
  ✅ Helps debug input data issues
```

---

## Quick Start

### 1. Train the Model (ONE TIME)
```bash
python train_salary_model.py
```
This creates the trained model files in the `models/` directory.

### 2. Run Predictions
```bash
# Interactive mode
python main.py

# Or run example
python integration_example.py
```

### 3. View Results
- Placement probability (5%-100%)
- Service/Product probabilities
- Single salary prediction
- **NEW: Salary tier distribution with probabilities**

---

## Files Modified

1. **[main.py](main.py)**
   - Added import: `from modules.salary_probability import SalaryTierPredictor`
   - Modified `calculate_placement_probabilities()`: Added STEP 4B for salary tier prediction
   - Modified `display_results()`: Added salary tier distribution display
   - Return dict: Added `'salary_distribution'` key

2. **[modules/salary_probability.py](modules/salary_probability.py)**
   - Fixed `train_salary_model()`: Now creates derived features automatically
   - Fixed `predict_salary_distribution()`: Now creates derived features in prediction
   - Updated `save_model()`: Now saves feature names
   - Updated `load_model()`: Now loads feature names
   - Improved error handling: Better error messages

3. **[train_salary_model.py](train_salary_model.py)** (NEW)
   - Complete training pipeline
   - Loads 4000-student dataset with salary_lpa column
   - Trains on 2000 placed students
   - Saves model, scaler, features

4. **[integration_example.py](integration_example.py)** (NEW)
   - Complete demonstration of integration
   - Shows all 7 prediction steps
   - Example input/output
   - Educational walkthrough of system

---

## Technical Specifications

### XGBoost Configuration
```python
XGBClassifier(
    objective="multi:softprob",      # Multi-class probability
    num_class=7,                      # 7 salary tiers
    n_estimators=200,                 # 200 trees
    max_depth=4,                      # Tree depth limit
    learning_rate=0.05,               # Conservative learning
    subsample=0.7,                    # 70% data per tree
    colsample_bytree=0.7,             # 70% features per tree
    random_state=42,                  # Reproducibility
    eval_metric='mlogloss'            # Multi-class loss
)
```

### Feature Normalization
```python
# StandardScaler applied to ALL 10 features
scaler.fit_transform(X)  # Training
scaler.transform(X)       # Prediction
```

### Probability Bounds
```python
# Raw probabilities from model
probabilities = [0.0, 0.0, ...., 1.0]  # Shape: (7,)

# Formatted output
{"0-5 LPA": 0.1, "5-10 LPA": 15.3, ...}  # Percentages
```

---

## Summary

✅ **Integration Complete!**

The salary tier prediction model has been successfully:
- **Trained** on 2000 placed students
- **Saved** to disk with all necessary components
- **Integrated** into main.py prediction pipeline
- **Tested** with example student data
- **Documented** with comprehensive guides

**Ready to use:** Run `python main.py` to get salary tier predictions along with placement, company type, and single salary value predictions!
