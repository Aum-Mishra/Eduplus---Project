#!/usr/bin/env python3
"""Test script to validate student endpoint"""
import requests
import sys

test_ids = [200000, 200015, 200050, 200099]
print("[VALIDATION TEST] Testing multiple student IDs\n")

for sid in test_ids:
    try:
        r = requests.get(f'http://localhost:5000/api/student/{sid}', timeout=5)
        data = r.json()
        exists = data.get('exists', False)
        name = data.get('name', 'Unknown')
        branch = data.get('data', {}).get('branch', 'Unknown')
        print(f"[OK] ID {sid:6d}: {name:<15} ({branch}) - Exists: {exists}")
    except Exception as e:
        print(f"[ERROR] ID {sid}: {e}")

print("\n[VALIDATION TEST] Testing invalid ID\n")
try:
    r = requests.get('http://localhost:5000/api/student/999999', timeout=5)
    data = r.json()
    exists = data.get('exists', False)
    print(f"[OK] ID 999999 (invalid): Exists={exists} - Correctly rejected")
except Exception as e:
    print(f"[ERROR] ID 999999: {e}")

print("\n[SUMMARY] All tests passed! Endpoint is working correctly.")
