"""
COMPLETE INTEGRATION EXAMPLE - Salary Tier Prediction with Placement Probabilities
Shows how the salary tier model is integrated into the main prediction pipeline
"""

import pandas as pd
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from modules.ml_models import MLModels
from modules.feature_engineering import FeatureEngineering
from modules.service_product_probability import ServiceProductProbability
from modules.salary_probability import SalaryTierPredictor

def run_integration_example():
    """
    Run complete integration example showing:
    1. Loading a student
    2. Calculating placement probability
    3. Calculating service/product probabilities
    4. Calculating salary tier distribution
    5. Displaying all results
    """
    
    print("\n" + "="*70)
    print("COMPLETE INTEGRATION EXAMPLE".center(70))
    print("Placement Prediction System with Salary Tier Distribution".center(70))
    print("="*70)
    
    # ========== STEP 1: LOAD SAMPLE STUDENT DATA ==========
    print("\n" + "="*70)
    print("[STEP 1] LOADING SAMPLE STUDENT DATA")
    print("="*70)
    
    # Sample student data
    student_data = {
        'student_id': 200005,
        'name': 'Sample_Student',
        'branch': 'CSE',
        'cgpa': 8.2,
        'os_score': 75.5,
        'dbms_score': 72.3,
        'cn_score': 68.9,
        'oop_score': 79.1,
        'system_design_score': 71.2,
        'cs_fundamentals_score': 74.2,
        'project_score': 82.5,
        'dsa_score': 85.3,
        'aptitude_score': 78.5,
        'hr_score': 81.2,
        'resume_ats_score': 76.8,
        'hackathon_wins': 1
    }
    
    print(f"\nStudent ID: {student_data['student_id']}")
    print(f"Name: {student_data['name']}")
    print(f"CGPA: {student_data['cgpa']}")
    print(f"\nKey Scores:")
    print(f"  • DSA Score: {student_data['dsa_score']}")
    print(f"  • Project Score: {student_data['project_score']}")
    print(f"  • Aptitude Score: {student_data['aptitude_score']}")
    print(f"  • HR Score: {student_data['hr_score']}")
    print(f"  • ATS Score: {student_data['resume_ats_score']}")
    
    # ========== STEP 2: LOAD ML MODELS ==========
    print("\n" + "="*70)
    print("[STEP 2] LOADING ML MODELS")
    print("="*70)
    
    try:
        models_obj = MLModels()
        if models_obj.load_models():
            print("✅ Placement ML models loaded successfully!")
        else:
            print("❌ Failed to load models")
            return False
        
        # Initialize feature engineering
        fe = FeatureEngineering()
        fe.fitted = True
        fe.scaler = models_obj.scaler
        print("✅ Feature engineering module initialized!")
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False
    
    # ========== STEP 3: FEATURE ENGINEERING ==========
    print("\n" + "="*70)
    print("[STEP 3] FEATURE ENGINEERING & PREPARATION")
    print("="*70)
    
    try:
        # Prepare student features
        student_features = fe.prepare_student_input(student_data)
        print("✅ Features prepared and scaled!")
        print(f"   Feature vector dimension: {len(student_features)}")
        
    except Exception as e:
        print(f"❌ Error in feature preparation: {e}")
        return False
    
    # ========== STEP 4: PLACEMENT PROBABILITY ==========
    print("\n" + "="*70)
    print("[STEP 4] PLACEMENT PROBABILITY PREDICTION")
    print("="*70)
    
    try:
        # Get ML model raw probability
        raw_prob = models_obj.placement_model.predict_proba([student_features])[0][1]
        print(f"Raw ML Probability: {raw_prob:.4f}")
        
        # Apply penalty adjustments
        skill_avg = (student_data['dsa_score'] + student_data['project_score'] +
                    student_data['cs_fundamentals_score']) / 3
        soft_avg = (student_data['aptitude_score'] + student_data['hr_score']) / 2
        
        print(f"\nPenalty Assessment:")
        print(f"  • Skill Average: {skill_avg:.1f}")
        print(f"  • Soft Skills Average: {soft_avg:.1f}")
        print(f"  • CGPA: {student_data['cgpa']}")
        
        p = raw_prob
        apply_penalties = []
        
        if skill_avg < 40:
            p *= 0.4
            apply_penalties.append("⚠️  Skill penalty (×0.4)")
        if soft_avg < 40:
            p *= 0.6
            apply_penalties.append("⚠️  Soft skills penalty (×0.6)")
        if student_data['cgpa'] < 6:
            p *= 0.5
            apply_penalties.append("⚠️  CGPA penalty (×0.5)")
        
        if apply_penalties:
            print(f"\nPenalties Applied:")
            for penalty in apply_penalties:
                print(f"  {penalty}")
        else:
            print(f"\n✅ No penalties applied!")
        
        # Apply smoothing
        ml_placement_prob = max(0.05, min(1.0, p))
        print(f"\nFinal Placement Probability: {ml_placement_prob*100:.2f}%")
        print(f"(Range: 5% - 100% after smoothing)")
        
    except Exception as e:
        print(f"❌ Error calculating placement probability: {e}")
        return False
    
    # ========== STEP 5: SERVICE/PRODUCT PROBABILITIES ==========
    print("\n" + "="*70)
    print("[STEP 5] SERVICE vs PRODUCT COMPANY PROBABILITY")
    print("="*70)
    
    try:
        sp_calc = ServiceProductProbability()
        sp_result = sp_calc.get_company_type_probability(ml_placement_prob, student_data)
        
        service_prob = sp_result['service_probability']
        product_prob = sp_result['product_probability']
        
        print(f"Service-Based Companies: {service_prob:.2f}%")
        print(f"Product-Based Companies: {product_prob:.2f}%")
        
        diff = abs(product_prob - service_prob)
        if diff > 1:
            if product_prob > service_prob:
                print(f"\n✅ Student is {diff:.2f}% better suited for PRODUCT companies")
            else:
                print(f"\n✅ Student is {diff:.2f}% better suited for SERVICE companies")
        else:
            print(f"\n✅ Student is equally suited for both company types")
        
    except Exception as e:
        print(f"❌ Error calculating company probabilities: {e}")
        return False
    
    # ========== STEP 6: SALARY PREDICTION (Single Value) ==========
    print("\n" + "="*70)
    print("[STEP 6] SALARY PREDICTION (ML Regression Model)")
    print("="*70)
    
    try:
        if models_obj.salary_model:
            salary_pred = models_obj.salary_model.predict([student_features])[0]
            print(f"Predicted Salary (XGBRegressor): {salary_pred:.2f} LPA")
        else:
            salary_pred = None
            print("⚠️  Regression model not available")
    except Exception as e:
        print(f"❌ Error predicting salary: {e}")
        salary_pred = None
    
    # ========== STEP 7: SALARY TIER DISTRIBUTION ==========
    print("\n" + "="*70)
    print("[STEP 7] SALARY TIER DISTRIBUTION (NEW INTEGRATION)")
    print("="*70)
    
    try:
        salary_predictor = SalaryTierPredictor()
        
        if salary_predictor.load_model():
            print("✅ Salary tier model loaded successfully!")
            print(f"   Model location: models/salary_tier_model.pkl")
            print(f"   Scaler location: models/salary_tier_scaler.pkl")
            
            # Predict salary tier distribution
            salary_distribution = salary_predictor.predict_salary_distribution(student_data)
            
            if salary_distribution:
                print("\n💰 SALARY TIER PROBABILITY DISTRIBUTION:")
                print("-" * 50)
                
                # Sort by probability (descending)
                sorted_tiers = sorted(salary_distribution.items(), key=lambda x: x[1], reverse=True)
                
                for tier, prob in sorted_tiers:
                    bar_length = int(prob / 5)
                    bar = "█" * bar_length
                    print(f"  {tier:12} → {prob:6.1f}% {bar}")
                
                print("-" * 50)
                
                # Composite probabilities
                above_15_lpa = (salary_distribution.get("15-20 LPA", 0) + 
                               salary_distribution.get("20-30 LPA", 0) + 
                               salary_distribution.get("30-40 LPA", 0) + 
                               salary_distribution.get(">40 LPA", 0))
                
                above_20_lpa = (salary_distribution.get("20-30 LPA", 0) + 
                               salary_distribution.get("30-40 LPA", 0) + 
                               salary_distribution.get(">40 LPA", 0))
                
                above_40_lpa = salary_distribution.get(">40 LPA", 0)
                
                print(f"\n📊 SALARY THRESHOLDS:")
                print(f"  • Probability of earning >15 LPA: {above_15_lpa:.1f}%")
                print(f"  • Probability of earning >20 LPA: {above_20_lpa:.1f}%")
                print(f"  • Probability of earning >40 LPA: {above_40_lpa:.1f}%")
                
                # Most likely tier
                most_likely_tier = max(salary_distribution, key=salary_distribution.get)
                most_likely_prob = salary_distribution[most_likely_tier]
                print(f"\n🎯 MOST LIKELY SALARY RANGE:")
                print(f"   {most_likely_tier} with {most_likely_prob:.1f}% probability")
            else:
                print("❌ Failed to predict salary distribution")
                salary_distribution = None
        else:
            print("⚠️  Salary tier model not found!")
            print("    Run: python train_salary_model.py")
            salary_distribution = None
            
    except Exception as e:
        print(f"❌ Error with salary tier prediction: {e}")
        import traceback
        traceback.print_exc()
        salary_distribution = None
    
    # ========== STEP 8: FINAL SUMMARY ==========
    print("\n" + "="*70)
    print("FINAL PREDICTION SUMMARY".center(70))
    print("="*70)
    
    print(f"\n📋 STUDENT INFORMATION:")
    print(f"   ID: {student_data['student_id']}")
    print(f"   Name: {student_data['name']}")
    print(f"   CGPA: {student_data['cgpa']:.2f}/10")
    
    print(f"\n📊 PLACEMENT PREDICTIONS:")
    print(f"   Overall Placement Probability: {ml_placement_prob*100:.2f}%")
    print(f"   Service Companies Probability: {service_prob:.2f}%")
    print(f"   Product Companies Probability: {product_prob:.2f}%")
    
    print(f"\n💰 SALARY PREDICTIONS:")
    if salary_pred:
        print(f"   Predicted Salary (Regression): {salary_pred:.2f} LPA")
    else:
        print(f"   Predicted Salary (Regression): Not available")
    
    if salary_distribution:
        most_likely = max(salary_distribution, key=salary_distribution.get)
        print(f"   Most Likely Salary Range: {most_likely}")
        print(f"   Probability: {salary_distribution[most_likely]:.1f}%")
    else:
        print(f"   Salary Tier Distribution: Not available")
    
    print("\n" + "="*70)
    print("✅ INTEGRATION COMPLETE AND WORKING!".center(70))
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = run_integration_example()
    sys.exit(0 if success else 1)
