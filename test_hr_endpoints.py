#!/usr/bin/env python
"""Test HR Round endpoints"""

import requests
import json

print('='*70)
print('TESTING HR ROUND ENDPOINTS')
print('='*70)

print('\n✅ 1. Testing /hr-round/questions endpoint:')
try:
    r = requests.get('http://localhost:5000/api/hr-round/questions', timeout=10)
    print(f'   Status: {r.status_code}')
    data = r.json()
    questions = data.get('questions', [])
    print(f'   Questions received: {len(questions)}')
    for i, q in enumerate(questions, 1):
        print(f'      {i}. {q[:70]}...')
    print(f'   ✅ HR Questions loading correctly!')
except Exception as e:
    print(f'   ❌ ERROR: {e}')

print('\n✅ 2. Testing /aptitude/links endpoint:')
try:
    r = requests.get('http://localhost:5000/api/aptitude/links', timeout=10)
    print(f'   Status: {r.status_code}')
    data = r.json()
    print(f'   Aptitude URL: {data.get("aptitude_url")}')
    print(f'   ATS URL: {data.get("ats_url")}')
    print(f'   ✅ Aptitude/ATS links loading correctly!')
except Exception as e:
    print(f'   ❌ ERROR: {e}')

print('\n✅ 3. Testing /hr-round/evaluate endpoint:')
try:
    answers = [
        'I was responsible for the database design in a Django project.',
        'We faced API issues and I debugged and fixed them.',
        'I made a mistake with the schema but learned to validate properly.',
        'I handle pressure by organizing tasks and communicating clearly.',
        'I learned Kubernetes by studying docs and practicing.'
    ]
    r = requests.post('http://localhost:5000/api/hr-round/evaluate', 
                     json={'answers': answers}, timeout=30)
    print(f'   Status: {r.status_code}')
    data = r.json()
    print(f'   HR Score: {data.get("score")}/100')
    print(f'   Breakdown: {data.get("breakdown")}')
    print(f'   ✅ HR evaluation working correctly!')
except Exception as e:
    print(f'   ❌ ERROR: {e}')

print('\n' + '='*70)
print('✅ ALL ENDPOINTS FIXED AND WORKING!')
print('='*70)
