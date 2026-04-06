import pandas as pd
import re
from pathlib import Path

path = Path('data/company_placement_db.csv')
if not path.exists():
    path = Path('Chatbot/data/company_placement_db.csv')

df = pd.read_csv(path)

# normalize fields similar to action logic
for c in ['avg_package_lpa','max_package_lpa','min_cgpa','hiring_intensity']:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

if 'max_backlogs' in df.columns:
    df['backlogs_allowed'] = pd.to_numeric(df['max_backlogs'], errors='coerce').fillna(0).astype(int)
else:
    def _bl(v):
        try:
            return int(float(str(v)))
        except Exception:
            return 1 if str(v).strip().lower() == 'true' else 0
    df['backlogs_allowed'] = df.get('backlogs_allowed', 0).apply(_bl)

def round_count(row):
    txt = str(row.get('interview_process',''))
    nums = [int(x) for x in re.findall(r'round\s*(\d+)|(?:^|\D)(\d+)\s*round', txt.lower()) for x in x if x]
    if nums:
        return max(nums)
    parts = re.split(r'[;,.|]+', txt)
    parts = [p.strip() for p in parts if p.strip()]
    return len(parts) if parts else 3

df['round_count'] = df.apply(round_count, axis=1)

def split_items(s):
    s = str(s).replace(';', ',').replace('|', ',')
    return [x.strip() for x in s.split(',') if x.strip() and x.strip().upper()!='NA']

print('Q1 Tier-1, >20 LPA, CGPA >8')
q1 = df[df['company_tier'].astype(str).str.contains('tier-1', case=False, na=False) & (df['avg_package_lpa'] > 20) & (df['min_cgpa'] > 8)][['company_name','avg_package_lpa','min_cgpa']].sort_values('avg_package_lpa', ascending=False).head(10)
print(q1.to_string(index=False))

print('\nQ2 High hiring intensity + fewer rounds')
q2 = df[df['hiring_intensity'] >= df['hiring_intensity'].median()].sort_values(['round_count','hiring_intensity'], ascending=[True,False])[['company_name','hiring_intensity','round_count']].head(10)
print(q2.to_string(index=False))

print('\nQ3 High salary + allow backlogs')
q3 = df[df['backlogs_allowed']>0].sort_values('max_package_lpa', ascending=False)[['company_name','max_package_lpa','backlogs_allowed']].head(10)
print(q3.to_string(index=False))

print('\nQ4 Require strong DSA + System Design')
q4 = df[df['required_skills'].astype(str).str.lower().str.contains('dsa|data structures', regex=True, na=False) & df['required_skills'].astype(str).str.lower().str.contains('system|design', regex=True, na=False)][['company_name','required_skills']].head(10)
if q4.empty:
    q4 = df[df['prep_system_design_topics'].astype(str).str.upper().ne('NA') & df['prep_dsa_topics'].astype(str).str.upper().ne('NA')][['company_name','prep_dsa_topics','prep_system_design_topics']].head(10)
print(q4.to_string(index=False))

print('\nQ5 Best for CSE with 7 CGPA')
dept_mask = df['allowed_departments'].astype(str).str.lower().str.contains('cse|computer science|all', regex=True, na=False)
q5 = df[dept_mask & (df['min_cgpa'] <= 7.0)].copy()
if q5.empty:
    q5 = df[dept_mask].copy()
q5['fit_score'] = (q5['avg_package_lpa'] * 1.3) + q5['hiring_intensity'] - (q5['round_count'] * 0.7) - (q5['min_cgpa'] - 7.0).abs()
print(q5.sort_values('fit_score', ascending=False)[['company_name','avg_package_lpa','min_cgpa','round_count']].head(10).to_string(index=False))

print('\nQ6 Best package with lowest CGPA requirement')
q6 = df.copy()
q6['package_cgpa_ratio'] = q6['max_package_lpa'] / q6['min_cgpa'].replace(0,1)
print(q6.sort_values(['package_cgpa_ratio','max_package_lpa'], ascending=[False,False])[['company_name','max_package_lpa','min_cgpa','package_cgpa_ratio']].head(10).to_string(index=False))

print('\nQ7 High packages + short interview process')
q7 = df.copy()
q7['short_process_score'] = q7['max_package_lpa'] - (q7['round_count'] * 1.5)
print(q7.sort_values(['short_process_score','max_package_lpa'], ascending=[False,False])[['company_name','max_package_lpa','round_count']].head(10).to_string(index=False))

print('\nQ8 Most preparation topics')
prep_cols = ['prep_dsa_topics','prep_system_design_topics','prep_oops_topics','prep_dbms_topics','prep_hr_topics']
def topic_count(row):
    ct = 0
    for c in prep_cols:
        v = str(row.get(c,'')).strip()
        if v and v.upper() != 'NA':
            ct += len(split_items(v)) or 1
    return ct
q8 = df.copy()
q8['prep_topic_count'] = q8.apply(topic_count, axis=1)
print(q8.sort_values('prep_topic_count', ascending=False)[['company_name','prep_topic_count']].head(10).to_string(index=False))
