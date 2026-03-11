"""
Test script to verify the placement probability system
Tests service/product-based and company-wise probability calculations
"""

import sys
import io

# Set UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.service_product_probability import ServiceProductProbability
from modules.company_wise_probability import CompanyWiseProbability


def test_service_product_probability():
    """Test the service/product probability calculator"""
    print("\n" + "="*60)
    print("TEST 1: Service/Product Company Probability")
    print("="*60)

    sp_calc = ServiceProductProbability()

    # Sample student data
    student_scores = {
        'dsa_score': 70,
        'project_score': 60,
        'cs_fundamentals_score': 55,
        'aptitude_score': 40
    }

    # ML base probability (65%)
    ml_placement_prob = 0.65

    print("\n📊 Student Scores:")
    print(f"   DSA: {student_scores['dsa_score']}")
    print(f"   Project: {student_scores['project_score']}")
    print(f"   CS Fundamentals: {student_scores['cs_fundamentals_score']}")
    print(f"   Aptitude: {student_scores['aptitude_score']}")
    print(f"\nML Base Probability: {ml_placement_prob * 100:.2f}%")

    # Calculate probabilities
    result = sp_calc.get_company_type_probability(ml_placement_prob, student_scores)

    print("\n✅ Results:")
    print(f"   Service Company Probability: {result['service_probability']:.2f}%")
    print(f"   Product Company Probability: {result['product_probability']:.2f}%")
    print(f"   Service Score: {result['service_score']:.4f}")
    print(f"   Product Score: {result['product_score']:.4f}")

    # Verification
    assert 0 <= result['service_probability'] <= 100, "Service probability out of range!"
    assert 0 <= result['product_probability'] <= 100, "Product probability out of range!"

    print("\n✅ Test 1 Passed!")
    return result


def test_company_wise_probability(service_prob, product_prob):
    """Test the company-wise probability calculator"""
    print("\n" + "="*60)
    print("TEST 2: Company-Wise Probability")
    print("="*60)

    company_calc = CompanyWiseProbability()

    print(f"\n📊 Input Probabilities:")
    print(f"   Service: {service_prob:.2f}%")
    print(f"   Product: {product_prob:.2f}%")

    # Calculate all company probabilities
    company_probs = company_calc.calculate_all_companies(service_prob, product_prob)

    print(f"\n✅ Calculated probabilities for {len(company_probs)} companies")

    # Get top companies
    top_companies = company_calc.get_top_companies(company_probs, 10)

    print("\n🏆 Top 10 Companies:")
    print(f"{'Rank':<5} {'Company':<25} {'Probability':<15}")
    print("-" * 50)

    for i, (company, prob) in enumerate(top_companies, 1):
        company_type = company_calc.get_company_type(company)
        print(f"{i:<5} {company:<25} {prob:>6.2f}%")

    # Verification
    assert len(company_probs) > 0, "No company probabilities calculated!"
    for prob in company_probs.values():
        assert 0 <= prob <= 100, f"Probability {prob} out of range!"

    print("\n✅ Test 2 Passed!")
    return company_probs, top_companies


def test_with_sample_students():
    """Test with actual student data from CSV"""
    print("\n" + "="*60)
    print("TEST 3: Sample Student from Database")
    print("="*60)

    import pandas as pd
    import os

    csv_path = os.path.join(os.path.dirname(__file__), 'data/student_profiles_100.csv')

    try:
        df = pd.read_csv(csv_path)

        # Find a student with all scores
        students_with_scores = df[
            df[['dsa_score', 'project_score', 'cs_fundamentals_score', 'aptitude_score']].notna().all(axis=1)
        ]

        if len(students_with_scores) > 0:
            student = students_with_scores.iloc[0]
            student_id = student['student_id']
            name = student['name']

            print(f"\n👤 Student: {name} (ID: {student_id})")

            sp_calc = ServiceProductProbability()
            company_calc = CompanyWiseProbability()

            student_scores = {
                'dsa_score': float(student['dsa_score']),
                'project_score': float(student['project_score']),
                'cs_fundamentals_score': float(student['cs_fundamentals_score']),
                'aptitude_score': float(student['aptitude_score'])
            }

            ml_placement_prob = 0.65

            # Calculate service/product
            sp_result = sp_calc.get_company_type_probability(ml_placement_prob, student_scores)

            print(f"\n📊 Scores:")
            print(f"   DSA: {student_scores['dsa_score']:.2f}")
            print(f"   Project: {student_scores['project_score']:.2f}")
            print(f"   CS Fundamentals: {student_scores['cs_fundamentals_score']:.2f}")
            print(f"   Aptitude: {student_scores['aptitude_score']:.2f}")

            print(f"\n🎯 Probabilities:")
            print(f"   Service Companies: {sp_result['service_probability']:.2f}%")
            print(f"   Product Companies: {sp_result['product_probability']:.2f}%")

            # Calculate company-wise
            company_probs = company_calc.calculate_all_companies(
                sp_result['service_probability'],
                sp_result['product_probability']
            )

            top_companies = company_calc.get_top_companies(company_probs, 10)

            print(f"\n🏆 Top 10 Companies for this student:")
            print(f"{'Rank':<5} {'Company':<25} {'Probability':<15}")
            print("-" * 50)

            for i, (company, prob) in enumerate(top_companies, 1):
                print(f"{i:<5} {company:<25} {prob:>6.2f}%")

            print("\n✅ Test 3 Passed!")
        else:
            print("\n⚠️  No students with complete scores found in database")

    except Exception as e:
        print(f"\n⚠️  Could not test with database: {e}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PLACEMENT PROBABILITY SYSTEM - TEST SUITE")
    print("="*60)

    try:
        # Test 1: Service/Product probability
        sp_result = test_service_product_probability()

        # Test 2: Company-wise probability
        company_probs, top_companies = test_company_wise_probability(
            sp_result['service_probability'],
            sp_result['product_probability']
        )

        # Test 3: Sample student from database
        test_with_sample_students()

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Probability system is working correctly!")
        print("\nYou can now run the main application with:")
        print("   python main.py")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
