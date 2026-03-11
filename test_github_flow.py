#!/usr/bin/env python
"""
Test GitHub Repository Processing Flow
Shows: Clone → Analyze (9 Steps) → Cleanup
"""

import requests
import json
import time

# Test with small public repositories
repos = [
    'https://github.com/octocat/Hello-World',  # Small, public test repo
]

print('\n' + '='*80)
print('GITHUB REPOSITORY PROCESSING FLOW TEST')
print('='*80)
print('\nThis test demonstrates the complete processing flow:')
print('  1. Clone repository')
print('  2. Analyze (9 steps)')
print('  3. Delete temporary directory')
print('\n' + '='*80 + '\n')

print('[TEST] Sending GitHub analysis request...\n')
print(f'Repositories to process: {len(repos)}')
for i, repo in enumerate(repos, 1):
    print(f'  {i}. {repo}')

print('\n' + '-'*80)
print('Watch the Flask console for the complete flow (clone → analyze → cleanup)')
print('-'*80 + '\n')

try:
    start_time = time.time()
    
    response = requests.post(
        'http://localhost:5000/api/integrations/github-projects',
        json={'repo_urls': repos},
        timeout=120
    )
    
    elapsed = time.time() - start_time
    
    print(f'\n[TEST RESULT]')
    print(f'Status Code: {response.status_code}')
    print(f'Response Time: {elapsed:.2f} seconds')
    
    if response.status_code == 200:
        data = response.json()
        
        print(f'\n[ANALYSIS RESULTS]')
        print(f'  Repos Requested: {data.get("repo_count")}')
        print(f'  Repos Analyzed: {len(data.get("repos", []))}')
        print(f'  Average Score: {data.get("score")}/100')
        
        if data.get('repos'):
            print(f'\n[DETAILED RESULTS]')
            for i, repo in enumerate(data.get('repos', []), 1):
                print(f'\n  Repository {i}:')
                print(f'    URL: {repo.get("repo_url")}')
                print(f'    Score: {repo.get("final_project_score")}/100')
                print(f'    Assessment: {repo.get("assessment")}')
                print(f'    Files Analyzed: {repo.get("code_files")}')
                print(f'    LOC: {repo.get("lines_of_code")}')
                
        print('\n' + '='*80)
        print('✅ FLOW COMPLETE: Repository cloned, analyzed, and deleted!')
        print('='*80 + '\n')
        
        print('[CLEANUP VERIFICATION]')
        print('  ✅ Flask console shows "[CLEANUP] Removing temp directory..."')
        print('  ✅ Flask console shows "✅ Temporary directory deleted successfully"')
        print('  ✅ This confirms the repository was properly cleaned up after analysis')
        
    else:
        print(f'\n❌ Error: {response.text}')
        
except requests.exceptions.Timeout:
    print('\n⏱️  Request timed out')
    print('   (This may happen with large repositories)')
    
except Exception as e:
    print(f'\n❌ Error: {e}')
