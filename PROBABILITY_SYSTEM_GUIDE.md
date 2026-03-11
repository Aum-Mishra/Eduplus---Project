# Placement Probability System - Redesigned for Service & Product-Based Companies

## Overview

This document describes the redesigned placement probability system that now distinguishes between **service-based** and **product-based** companies, providing more accurate placement predictions for each company type.

## Architecture

### System Components

#### 1. **Service/Product Probability Module** (`modules/service_product_probability.py`)
Calculates the probability of placement in service-based vs product-based companies based on student skills.

**Key Features:**
- Service company weight formula with emphasis on aptitude (35%) and DSA (35%)
- Product company weight formula with emphasis on DSA (45%) and projects (30%)
- ML blending factor (α = 0.6) to combine model predictions with skill-based logic
- Normalization of scores to 0-100 percentage range

#### 2. **Company-Wise Probability Module** (`modules/company_wise_probability.py`)
Calculates placement probability for each individual company using difficulty factors.

**Key Features:**
- Loads company profiles from `company_profiles_with_difficulty.csv`
- Applies company-specific difficulty factors to adjust probabilities
- Maps companies to service/product/hybrid types
- Ranks companies by placement probability

#### 3. **Updated Prediction Module** (`modules/prediction.py`)
Integrates both probability modules into the main prediction workflow.

## Data Flow

```
Student Profile (student_profiles_100.csv)
    ↓
Service/Product Probability Calculator
    ├── Calculates Service Score (weighted: aptitude, DSA, CS fundamentals, projects)
    ├── Calculates Product Score (weighted: DSA, projects, CS fundamentals, aptitude)
    └── Blends with ML model probability
    ↓
Company-Wise Probability Calculator
    ├── Gets service/product probabilities
    ├── Retrieves company difficulty factors
    ├── Calculates probability for each company
    └── Ranks companies by probability
    ↓
Results Stored in student_profiles_100.csv
    ├── overall_placement_probability
    ├── service_company_probability
    ├── product_company_probability
    └── Individual company probabilities (top 15)
```

## Probability Calculation Logic

### Step 1: Service-Based Company Score

```
Service_Score = 0.35 × aptitude + 0.35 × DSA + 0.15 × CS_fundamentals + 0.15 × projects
S_service = Service_Score / 100  (Normalized to 0-1)
```

**Why this weighting?**
- Service companies prioritize **aptitude** (35%) - measurement of analytical thinking
- Strong **DSA** (35%) - algorithmic problem-solving
- Less emphasis on advanced projects and CS theory

### Step 2: Product-Based Company Score

```
Product_Score = 0.45 × DSA + 0.30 × projects + 0.15 × CS_fundamentals + 0.10 × aptitude
S_product = Product_Score / 100  (Normalized to 0-1)
```

**Why this weighting?**
- Product companies heavily emphasize **DSA** (45%) - core requirement
- Strong **projects** (30%) - real-world engineering experience
- Less emphasis on aptitude (10%) - assume coding ability already tested

### Step 3: ML Blending Formula

```
P_service = α × P_base + (1 - α) × S_service
P_product = α × P_base + (1 - α) × S_product

Where α = 0.6 (60% ML weight, 40% skill-based weight)
```

**Result:** Hybrid approach combining:
- **ML Model** (60%): Learns from historical placement data
- **Domain Logic** (40%): Incorporates company-specific hiring patterns

### Step 4: Company-Specific Adjustment

```
P_company = P_company_type / difficulty_factor
Cap result to [0, 1] range
```

**Difficulty Factors:**
- Service companies: 0.9 (easier) - mass hiring, lower barriers
- Hybrid companies: 1.0 (moderate) - balanced requirements
- Product companies: 1.2-1.4 (harder) - elite hiring, high standards

**Example:**
```
Amazon (Product-Based, Difficulty = 1.4):
P_Amazon = 0.64 / 1.4 ≈ 0.53 → 53%

TCS (Service-Based, Difficulty = 0.9):
P_TCS = 0.61 / 0.9 ≈ 0.68 → 68%
```

## Output Format

### Overall Summary
```
Overall Placement Probability: 65%
  └─ Service-Based Companies: 61%
  └─ Product-Based Companies: 64%
```

### Company-Wise Breakdown
```
Company               Type        Probability
==============================================
TCS                   Service     68%
Infosys              Service     61%
Amazon               Product     53%
Microsoft            Product     49%
Google               Product     45%
```

### CSV Data
The updated `student_profiles_100.csv` includes:

**Original Columns:**
- student_id, name, branch, cgpa
- Academic scores (os_score, dbms_score, cn_score, oop_score, system_design_score)
- Skill scores (dsa_score, project_score, cs_fundamentals_score, aptitude_score)
- Soft skills (hr_score, resume_ats_score)

**New Columns:**
- `overall_placement_probability` - Base ML prediction (0-100%)
- `service_company_probability` - Service sector suitability (0-100%)
- `product_company_probability` - Product sector suitability (0-100%)
- `{Company}_probability` - Individual company-wise probability (15 top companies)

## How to Use

### 1. Updating Student Profiles
```bash
python update_profiles.py
```
This script:
- Reads from `student_profiles_100.csv`
- Calculates service/product/company probabilities
- Saves results back to the same CSV

### 2. Testing the System
```bash
python test_probabilities.py
```
Runs comprehensive tests:
- Service/Product probability calculations
- Company-wise probability calculations
- Sample student from database

### 3. Main Application
```bash
python main.py
```
- Enter student ID
- Collects/updates student data (DSA, projects, aptitude, HR scores)
- Generates comprehensive placement prediction
- Displays all probabilities and recommendations
- Updates `student_profiles_100.csv` with results

## Key Design Decisions

### 1. **Fetch from student_profiles_100, Don't Create New Files**
- Single source of truth
- Easier to manage and update
- No data duplication

### 2. **Use company_profiles_with_difficulty for All Company Logic**
- Centralized company information
- Easy to add/update companies
- Consistent difficulty factors across system

### 3. **Blending Factor (α = 0.6)**
- 60% ML model (learns from data)
- 40% Domain logic (company-specific patterns)
- Balanced approach: neither ML-only nor rule-only

### 4. **Difficulty Factors**
- Reflect actual company hiring competitiveness
- Adjust probabilities realistically
- Example: Google (1.4) is 56% harder than TCS (0.9)

## Example Walkthrough

### Student Profile:
```
Name: Student_1
DSA Score: 75.81
Project Score: 88.43
CS Fundamentals: 64.70
Aptitude Score: 52.96
ML Base Probability: 0.65 (65%)
```

### Calculation:

**Step 1: Service Score**
```
Service_Score = 0.35×52.96 + 0.35×75.81 + 0.15×64.70 + 0.15×88.43
              = 18.536 + 26.534 + 9.705 + 13.265
              = 68.04
S_service = 0.6804
```

**Step 2: Product Score**
```
Product_Score = 0.45×75.81 + 0.30×88.43 + 0.15×64.70 + 0.10×52.96
              = 34.115 + 26.529 + 9.705 + 5.296
              = 75.645
S_product = 0.7565
```

**Step 3: Blending**
```
P_service = 0.6×0.65 + 0.4×0.6804 = 0.39 + 0.2722 = 0.6622 → 66.22%
P_product = 0.6×0.65 + 0.4×0.7565 = 0.39 + 0.3026 = 0.6926 → 69.26%
```

**Step 4: Company-Specific**
```
TCS (Service, difficulty=0.9):        66.22% / 0.9 = 73.57%
Amazon (Product, difficulty=1.4):     69.26% / 1.4 = 49.47%
Google (Product, difficulty=1.4):     69.26% / 1.4 = 49.47%
```

### Insight:
"You are better suited for service-based companies (66.22%) than product-based (69.26%). However, your strong DSA and project skills give you 49-50% chances at top product companies like Amazon and Google. Service companies like TCS offer higher probability at 73.57%."

## Files Added/Modified

### New Files:
- `modules/service_product_probability.py` - Service/Product probability calculator
- `modules/company_wise_probability.py` - Company-wise probability calculator
- `update_profiles.py` - Script to update student profiles with probabilities
- `test_probabilities.py` - Test suite for probability system

### Modified Files:
- `modules/prediction.py` - Integrated new probability modules
- `data/student_profiles_100.csv` - Added probability columns

### Unchanged:
- `main.py` - Main application (works seamlessly with new modules)
- All other modules and data files

## Testing & Validation

The `test_probabilities.py` validates:
1. ✅ Service/Product probability calculations are within 0-100%
2. ✅ Company-wise probabilities are calculated for all companies
3. ✅ Top companies are ranked correctly
4. ✅ Sample student data produces expected results

## Troubleshooting

### Issue: "Loaded 0 company profiles"
- Check if `company_profiles_with_difficulty.csv` exists
- Verify file path is correct

### Issue: "Skipped 50 students"
- These students have missing DSA, project, aptitude, or CS fundamentals scores
- Run the main application to collect these scores

### Issue: Service and Product probabilities are similar
- Indicates balanced student profile across all skills
- Student is versatile and suited for both company types

## Future Enhancements

1. **Role-Based Probabilities** - Separate probabilities for different job roles
2. **Salary Prediction** - Company + role-specific salary predictions
3. **Internship Matching** - Preliminary internship probability before final year
4. **Skill Gap Analysis** - Identify which skills to improve for target company
5. **Batch Processing** - Process all 100 students and generate reports

## Summary

The redesigned system provides:
- ✅ **Accurate distinctions** between service and product companies
- ✅ **Company-specific probabilities** based on difficulty factors
- ✅ **Data consistency** - single source of truth (student_profiles_100.csv)
- ✅ **Domain logic** combined with ML for better predictions
- ✅ **Transparent calculations** - fully documented formulas
- ✅ **Easy integration** - seamless with existing main.py
