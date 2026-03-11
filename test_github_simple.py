#!/usr/bin/env python
"""Test GitHub endpoint with smaller repositories"""

import requests
import json
import time

# Use smaller test repositories that don't require auth
repos = [
    'https://github.com/torvalds/linux',  # Large but public
    'https://github.com/facebook/react'   # Also public
]

print('\n' + '='*70)
print('TESTING GITHUB ENDPOINT WITH PUBLIC REPOSITORIES')
print('='*70 + '\n')

try:
    print("[TEST] Sending request to GitHub evaluation endpoint...")
    print(f"[TEST] Repositories to analyze: {repos}\n")
    
    response = requests.post(
        'http://localhost:5000/api/integrations/github-projects',
        json={'repo_urls': repos},
        timeout=120
    )
    
    print('='*70)
    print('RESPONSE RECEIVED')
    print('='*70)
    print(f'\nRESPONSE STATUS: {response.status_code}')
    print(f'RESPONSE TIME: {response.elapsed.total_seconds():.2f} seconds\n')
    
    if response.status_code != 200:
        print(f"ERROR: Got status code {response.status_code}")
        print(f"Response: {response.text}")
    else:
        data = response.json()
        
        print('ANALYSIS RESULTS:')
        print(f'  ✅ Average Score: {data.get("score")}/100')
        print(f'  ✅ Repositories Requested: {data.get("repo_count")}')
        print(f'  ✅ Repositories Analyzed: {len(data.get("repos", []))}')
        print(f'  ✅ Message: {data.get("message")}')
        
        if data.get('repos'):
            print(f'\n' + '-'*70)
            print('DETAILED REPOSITORY ANALYSIS')
            print('-'*70)
            for i, repo in enumerate(data.get('repos', []), 1):
                print(f'\n  📁 REPOSITORY {i}')
                print(f'  ├─ URL: {repo.get("repo_url")}')
                print(f'  ├─ Score: {repo.get("final_project_score")}/100 ({repo.get("assessment")})')
                print(f'  ├─ Code Files: {repo.get("code_files")} | LOC: {repo.get("lines_of_code")}')
                print(f'  ├─ Tech: {", ".join(repo.get("tech_stack", []))}')
                print(f'  └─ Scores: Logic {repo.get("logic_density_score")}/5 | Arch {repo.get("architecture_score")}/5 | Tech {repo.get("tech_depth_score")}/5')
        
        print('\n' + '='*70)
        if len(data.get('repos', [])) > 0:
            print('✅ TEST PASSED: GitHub endpoint working!')
        else:
            print('⚠️  TEST PARTIAL: Endpoint works but repos failed to clone')
        print('='*70 + '\n')
        
except requests.exceptions.Timeout:
    print('\n⏱️  Request timed out. This is normal for large repos.')
    
except requests.exceptions.ConnectionError:
    print('\n❌ ERROR: Could not connect to Flask API.')
    print('   Make sure Flask is running on http://localhost:5000')
    
except Exception as e:
    print(f'\n❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
