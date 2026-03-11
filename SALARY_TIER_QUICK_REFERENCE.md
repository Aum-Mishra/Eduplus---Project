# **SALARY TIER PREDICTION - QUICK REFERENCE**

**Fast implementation guide for adding salary predictions to your system**

---

## **1-MINUTE SETUP**

### Step 1: Import the module
```python
from modules.salary_probability import SalaryTierPredictor
```

### Step 2: Create instance and load/train model
```python
salary_predictor = SalaryTierPredictor()

# Try to load existing model
if not salary_predictor.load_model():
    # If doesn't exist, train it
    df = pd.read_csv('data/student_profiles_100.csv')
    feature_names = ["cgpa", "project_score", "dsa_score", "hackathon_wins",
                     "aptitude_score", "hr_score", "resume_ats_score", "cs_fundamentals_score"]
    salary_predictor.train_salary_model(df, feature_names)
    salary_predictor.save_model()
```

### Step 3: Make predictions
```python
# Create student data
student = {
    'cgpa': 7.5, 'dsa_score': 75, 'project_score': 68,
    'cs_fundamentals_score': 72, 'aptitude_score': 80,
    'hr_score': 85, 'resume_ats_score': 78, 'hackathon_wins': 2
}

# Predict salary distribution
salary_dist = salary_predictor.predict_salary_distribution(student)

# Display
salary_predictor.print_salary_distribution(salary_dist)
```

---

## **COMMON USE CASES**

### **Question 1: "What is my probability of earning >20 LPA?"**

```python
# Get salary distribution
salary_dist = salary_predictor.predict_salary_distribution(student_data)

# Calculate probability
above_20_lpa = (salary_dist.get("20-30 LPA", 0) +
                salary_dist.get("30-40 LPA", 0) +
                salary_dist.get(">40 LPA", 0))

print(f"Your probability of earning >20 LPA: {above_20_lpa:.1f}%")
```

**Example Output:**
```
Your probability of earning >20 LPA: 14.5%
```

---

### **Question 2: "What salary range am I most likely to get?"**

```python
# Find most likely tier
most_likely = max(salary_dist, key=salary_dist.get)
prob = salary_dist[most_likely]

print(f"You are most likely to earn: {most_likely}")
print(f"With probability: {prob:.1f}%")
```

**Example Output:**
```
You are most likely to earn: 10-15 LPA
With probability: 42.3%
```

---

### **Question 3: "What is my probability of earning >40 LPA?"**

```python
above_40_lpa = salary_dist.get(">40 LPA", 0)
print(f"Probability of earning >40 LPA: {above_40_lpa:.1f}%")
```

**Example Output:**
```
Probability of earning >40 LPA: 2.3%
```

---

### **Question 4: "Show me the full salary distribution"**

```python
salary_predictor.print_salary_distribution(salary_dist)
```

**Example Output:**
```
============================================================
💰 SALARY TIER PROBABILITY DISTRIBUTION
============================================================
0-5 LPA      →   2.1% █
5-10 LPA     →  28.3% ███████
10-15 LPA    →  38.5% █████████
15-20 LPA    →  18.2% ████
20-30 LPA    →  10.1% ██
30-40 LPA    →   2.3% 
>40 LPA      →   0.5%

============================================================
📊 SALARY THRESHOLDS:
   Probability of salary > 15 LPA: 31.1%
   Probability of salary > 20 LPA: 13.0%
   Probability of salary > 40 LPA: 0.5%

🎯 MOST LIKELY SALARY RANGE:
   10-15 LPA with 38.5% probability
============================================================
```

---

### **Question 5: "My friend is getting paid ₹12 LPA. Is that good?"**

```python
# Check what tier matches this salary
tier = SalaryTierPredictor.salary_to_tier(12)
tier_label = SalaryTierPredictor.tier_to_salary_range(tier)
prob = salary_dist[tier_label]

print(f"Salary ₹12 LPA falls in tier: {tier_label}")
print(f"Your probability of getting this tier: {prob:.1f}%")

# Show position relative to you
if prob > 25:
    print("You are very likely to get this/better! ✓")
else:
    print("This is below your likely range. You can do better! 🚀")
```

---

## **INTEGRATION INTO MAIN SYSTEM**

### **In calculate_placement_probabilities() function:**

```python
def calculate_placement_probabilities(student_data):
    """Calculate placement + service/product + salary probabilities"""
    
    # ... existing placement & service/product code ...
    
    # NEW: Salary tier prediction
    print("\n[STEP 4] Predicting salary distribution...")
    try:
        salary_predictor = SalaryTierPredictor()
        
        if not salary_predictor.load_model():
            # Train if needed
            from train_models import train_all_models
            train_all_models()
            salary_predictor.load_model()
        
        # Predict
        salary_dist = salary_predictor.predict_salary_distribution(student_data)
        print(f"[OK] Salary distribution: {list(salary_dist.values())}")
        
    except Exception as e:
        print(f"[!] Salary prediction error: {e}")
        salary_dist = None
    
    return {
        'overall_placement_probability': ml_placement_prob * 100,
        'service_company_probability': service_prob,
        'product_company_probability': product_prob,
        'salary_distribution': salary_dist,  # ADD THIS
        'salary_prediction': salary_pred,
        'job_role_prediction': role_name,
    }
```

---

### **Display results:**

```python
def display_results(student_data, probabilities):
    """Display all results including salary distribution"""
    
    print("\n" + "="*60)
    print("PLACEMENT PREDICTION RESULTS")
    print("="*60)
    
    # ... existing code ...
    
    print("\n[SALARY DISTRIBUTION]")
    if probabilities.get('salary_distribution'):
        for tier, prob in probabilities['salary_distribution'].items():
            print(f"{tier:12} → {prob:6.1f}%")
    
    # Calculate composites
    salary_dist = probabilities['salary_distribution']
    above_20 = salary_dist.get("20-30 LPA", 0) + salary_dist.get("30-40 LPA", 0) + salary_dist.get(">40 LPA", 0)
    above_40 = salary_dist.get(">40 LPA", 0)
    
    print(f"\nProbability of > 20 LPA: {above_20:.1f}%")
    print(f"Probability of > 40 LPA: {above_40:.1f}%")
```

---

## **UTILITY FUNCTIONS**

### **Get all custom salary queries answered:**

```python
class SalaryQueries:
    """Utility class to answer common salary questions"""
    
    @staticmethod
    def above_salary(salary_dist, threshold_lpa):
        """Probability of earning above threshold"""
        mapping = {
            5: ["5-10 LPA", "10-15 LPA", "15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"],
            10: ["10-15 LPA", "15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"],
            15: ["15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"],
            20: ["20-30 LPA", "30-40 LPA", ">40 LPA"],
            30: ["30-40 LPA", ">40 LPA"],
            40: [">40 LPA"]
        }
        tiers = mapping.get(threshold_lpa, [])
        prob = sum(salary_dist.get(tier, 0) for tier in tiers)
        return prob
    
    @staticmethod
    def salary_range(salary_dist, min_lpa, max_lpa):
        """Probability of earning in specific range"""
        # Map salary range to tiers
        tier_mapping = {
            (0, 5): "0-5 LPA",
            (5, 10): "5-10 LPA",
            (10, 15): "10-15 LPA",
            (15, 20): "15-20 LPA",
            (20, 30): "20-30 LPA",
            (30, 40): "30-40 LPA",
            (40, float('inf')): ">40 LPA"
        }
        
        prob = 0
        for (tier_min, tier_max), tier_label in tier_mapping.items():
            if tier_max <= min_lpa or tier_min >= max_lpa:
                continue
            prob += salary_dist.get(tier_label, 0)
        return prob
    
    @staticmethod
    def most_likely_salary(salary_dist):
        """Get most likely salary tier"""
        return max(salary_dist, key=salary_dist.get)
    
    @staticmethod
    def salary_percentile(salary_dist):
        """Calculate salary percentiles"""
        cumulative = 0
        percentiles = {}
        for tier, prob in salary_dist.items():
            cumulative += prob
            percentiles[tier] = cumulative
        return percentiles

# Usage:
sq = SalaryQueries()

print(f"P(>20 LPA) = {sq.above_salary(salary_dist, 20):.1f}%")
print(f"P(15-20 LPA) = {sq.salary_range(salary_dist, 15, 20):.1f}%")
print(f"Most likely salary: {sq.most_likely_salary(salary_dist)}")

percentiles = sq.salary_percentile(salary_dist)
for tier, pct in percentiles.items():
    print(f"{tier}: {pct:.1f}th percentile")
```

---

## **ERROR HANDLING**

### **Safe salary prediction with fallback:**

```python
def safe_salary_prediction(student_data, feature_names):
    """Predict salary with error handling"""
    
    try:
        predictor = SalaryTierPredictor()
        
        # Load model
        if not predictor.load_model():
            raise Exception("Model not found")
        
        # Predict
        salary_dist = predictor.predict_salary_distribution(student_data)
        
        if salary_dist is None:
            raise Exception("Prediction returned None")
        
        return salary_dist
        
    except Exception as e:
        print(f"Warning: Could not predict salary ({e})")
        # Return default/uniform distribution
        return {
            "0-5 LPA": 14.3,
            "5-10 LPA": 14.3,
            "10-15 LPA": 14.3,
            "15-20 LPA": 14.3,
            "20-30 LPA": 14.3,
            "30-40 LPA": 14.3,
            ">40 LPA": 14.2
        }
```

---

## **BATCH PREDICTION**

### **Predict salary for multiple students:**

```python
def batch_predict_salaries(student_list, feature_names):
    """Predict salary distribution for multiple students"""
    
    predictor = SalaryTierPredictor()
    if not predictor.load_model():
        return None
    
    results = []
    for student in student_list:
        salary_dist = predictor.predict_salary_distribution(student)
        most_likely = max(salary_dist, key=salary_dist.get)
        above_20 = (salary_dist.get("20-30 LPA", 0) +
                    salary_dist.get("30-40 LPA", 0) +
                    salary_dist.get(">40 LPA", 0))
        
        results.append({
            'student_id': student.get('student_id'),
            'most_likely_salary': most_likely,
            'probability_above_20_lpa': above_20,
            'full_distribution': salary_dist
        })
    
    return results

# Usage:
students = [student1, student2, student3]
predictions = batch_predict_salaries(students, feature_names)

for pred in predictions:
    print(f"Student {pred['student_id']}: {pred['most_likely_salary']}")
```

---

## **COMPARISON WITH PEERS**

### **Compare student salary probability with class average:**

```python
def compare_salary_with_peers(student_salary_dist, class_avg_dist):
    """Compare individual vs class average salary distribution"""
    
    print("="*60)
    print("SALARY COMPARISON: YOU vs CLASS AVERAGE")
    print("="*60)
    
    for tier in student_salary_dist.keys():
        student_prob = student_salary_dist[tier]
        class_prob = class_avg_dist[tier]
        diff = student_prob - class_prob
        
        status = "↑" if diff > 2 else "↓" if diff < -2 else "="
        print(f"{tier:12} You: {student_prob:5.1f}% | Class: {class_prob:5.1f}% {status}")
    
    # Calculate percentile
    student_above_15 = sum(student_salary_dist.get(t, 0) 
                           for t in ["15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"])
    class_above_15 = sum(class_avg_dist.get(t, 0) 
                        for t in ["15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"])
    
    print(f"\nYour P(>15 LPA): {student_above_15:.1f}%")
    print(f"Class P(>15 LPA): {class_above_15:.1f}%")
    
    if student_above_15 > class_above_15:
        print(f"✓ You are {student_above_15 - class_above_15:.1f}% better than class average!")
    else:
        print(f"! You are {class_above_15 - student_above_15:.1f}% below class average")
```

---

## **JSON OUTPUT FORMAT**

### **Export salary predictions as JSON:**

```python
import json

def export_salary_as_json(student_id, salary_dist):
    """Export salary distribution as JSON"""
    
    data = {
        "student_id": student_id,
        "timestamp": pd.Timestamp.now().isoformat(),
        "salary_distribution": salary_dist,
        "analysis": {
            "most_likely_salary": max(salary_dist, key=salary_dist.get),
            "probability_above_15_lpa": sum(salary_dist.get(t, 0) 
                                           for t in ["15-20 LPA", "20-30 LPA", "30-40 LPA", ">40 LPA"]),
            "probability_above_20_lpa": sum(salary_dist.get(t, 0) 
                                           for t in ["20-30 LPA", "30-40 LPA", ">40 LPA"]),
            "probability_above_40_lpa": salary_dist.get(">40 LPA", 0)
        }
    }
    
    return json.dumps(data, indent=2)

# Usage:
json_output = export_salary_as_json(101, salary_dist)
print(json_output)
```

**Output:**
```json
{
  "student_id": 101,
  "timestamp": "2026-03-05T14:30:00",
  "salary_distribution": {
    "0-5 LPA": 2.1,
    "5-10 LPA": 28.3,
    "10-15 LPA": 38.5,
    "15-20 LPA": 18.2,
    "20-30 LPA": 10.1,
    "30-40 LPA": 2.3,
    ">40 LPA": 0.5
  },
  "analysis": {
    "most_likely_salary": "10-15 LPA",
    "probability_above_15_lpa": 31.1,
    "probability_above_20_lpa": 13.0,
    "probability_above_40_lpa": 0.5
  }
}
```

---

## **SUMMARY OF KEY METHODS**

```python
# Static utility methods
SalaryTierPredictor.salary_to_tier(12)                    # → 2
SalaryTierPredictor.tier_to_salary_range(2)               # → "10-15 LPA"

# Instance methods
predictor = SalaryTierPredictor()
predictor.train_salary_model(df, features)                # Train model
predictor.load_model()                                     # Load from disk
predictor.save_model()                                     # Save to disk
predictor.predict_salary_distribution(student_dict)       # Get probabilities
predictor.format_salary_output(raw_probs)                 # Format output
predictor.print_salary_distribution(formatted_dist)       # Pretty print
```

---

**That's it! You now have a complete salary prediction system! 💰**

