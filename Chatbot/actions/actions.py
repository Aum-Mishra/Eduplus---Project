import pandas as pd
from typing import Any, Text, Dict, List, Optional, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from fuzzywuzzy import process
import re
import os
from datetime import datetime
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Import placement prediction actions
try:
    from .actions_placement import (
        ActionGetPlacementProbability,
        ActionGetEligibleCompanies,
        ActionGetSkillGap
    )
    PLACEMENT_ACTIONS_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Could not import placement actions: {e}")
    PLACEMENT_ACTIONS_AVAILABLE = False

# INTERNAL PERSISTENT LOGGING FOR AUDIT
DEBUG_FILE = os.path.join(os.path.dirname(__file__), "../audit_debug.txt")

def log_debug(msg):
    try:
        with open(DEBUG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")
        print(msg) # Still print to terminal
    except Exception as e:
        print(f"[WARNING] Could not write to debug file: {e}")

# Clear log on startup (optional - comment out to keep logs)
# if os.path.exists(DEBUG_FILE):
#     os.remove(DEBUG_FILE)

# ==================== DATA PATHS ====================
# Centralised data directory at the project root (shared with Flask backend)
# Future CSV files for training should be placed in the same folder.
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "company_placement_db.csv")
ALT_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "company_placement_db.csv")
LEETCODE_DATA_DIR = os.path.join(DATA_DIR, "leetcode-companywise-interview-questions-master")
LEETCODE_REPORTS_DIR = os.path.join(DATA_DIR, "generated_reports")
LEETCODE_REPORT_BASE_URL = os.getenv("CHATBOT_REPORT_BASE_URL", "http://localhost:5000")

# ==================== GLOBAL DATA STORE ====================

class DataStore:
    """Singleton data loader for CSV"""
    _df = None
    _df_predictions = None
    _predictions_mtime = None
    _company_list = None
    _company_aliases = {
        'tcs': 'Tata Consultancy Services',
        'infy': 'Infosys',
        'micro': 'Microsoft',
        'ms': 'Microsoft',
        'goog': 'Google',
        'ggl': 'Google',
        'amzn': 'Amazon',
        'tcs': 'TCS',
        'infy': 'Infosys',
        'microsoft': 'Microsoft',
    }

    @staticmethod
    def _normalize_company_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize new company_placement_db schema to keep legacy actions working."""
        if df is None or df.empty:
            return pd.DataFrame()

        out = df.copy()

        # Canonical string cleanup
        if 'company_name' in out.columns:
            out['company_name'] = out['company_name'].astype(str).str.strip()

        # Legacy alias mapping
        if 'hiring_roles_description' in out.columns and 'job_role_notes' not in out.columns:
            out['job_role_notes'] = out['hiring_roles_description']

        if 'backlogs_allowed' in out.columns:
            out['backlogs_allowed'] = out['backlogs_allowed'].astype(str).str.strip().str.upper()

        # Use max_backlogs as the canonical numeric backlog limit for legacy actions.
        if 'max_backlogs' in out.columns:
            out['backlogs_allowed'] = pd.to_numeric(out['max_backlogs'], errors='coerce').fillna(0).astype(int)

        # Derive company category from tier label if missing.
        if 'company_cat' not in out.columns:
            def _derive_cat(tier_text):
                t = str(tier_text).lower()
                if 'product' in t:
                    return 'Product'
                if 'service' in t:
                    return 'Service'
                if 'hybrid' in t:
                    return 'Hybrid'
                return 'Hybrid'
            out['company_cat'] = out.get('company_tier', '').apply(_derive_cat)

        # Derive a normalized difficulty score when not present.
        if 'difficulty_factor' not in out.columns:
            def _derive_difficulty(row):
                tier = str(row.get('company_tier', '')).lower()
                intensity = float(row.get('hiring_intensity', 50) or 50)
                if 'tier-1' in tier:
                    base = 8.5
                elif 'tier-2' in tier:
                    base = 6.5
                else:
                    base = 5.0
                # Higher hiring intensity usually means slightly easier selection.
                adjust = 0.0
                if intensity >= 200:
                    adjust = -0.8
                elif intensity >= 100:
                    adjust = -0.4
                elif intensity <= 10:
                    adjust = 0.6
                return round(max(3.0, min(9.8, base + adjust)), 1)
            out['difficulty_factor'] = out.apply(_derive_difficulty, axis=1)

        # Provide default weight columns if not present in this dataset.
        missing_weights = any(col not in out.columns for col in ['weight_dsa', 'weight_projects', 'weight_cs', 'weight_aptitude', 'weight_hr'])
        if missing_weights:
            def _weights_from_tier(tier_text):
                t = str(tier_text).lower()
                if 'tier-1' in t:
                    return pd.Series([0.45, 0.25, 0.15, 0.10, 0.05])
                if 'tier-2' in t:
                    return pd.Series([0.30, 0.20, 0.20, 0.20, 0.10])
                return pd.Series([0.20, 0.15, 0.15, 0.30, 0.20])

            derived = out.get('company_tier', '').apply(_weights_from_tier)
            derived.columns = ['weight_dsa', 'weight_projects', 'weight_cs', 'weight_aptitude', 'weight_hr']
            for c in derived.columns:
                if c not in out.columns:
                    out[c] = derived[c]

        # Ensure prep topic columns exist.
        for col in ['prep_dsa_topics', 'prep_system_design_topics', 'prep_oops_topics', 'prep_dbms_topics', 'prep_hr_topics']:
            if col not in out.columns:
                out[col] = 'NA'

        return out

    @staticmethod
    def load_data(force_reload_predictions: bool = False):
        if DataStore._df is None:
            try:
                company_profile_path = CSV_PATH if os.path.exists(CSV_PATH) else ALT_CSV_PATH
                DataStore._df = pd.read_csv(company_profile_path)
                DataStore._df = DataStore._normalize_company_dataframe(DataStore._df)
                DataStore._company_list = DataStore._df['company_name'].tolist()
                print(f"[INFO] DataStore: Successfully loaded {len(DataStore._df)} company profiles.")
            except FileNotFoundError:
                print(f"[ERROR] DataStore: company_placement_db.csv not found at {CSV_PATH} or {ALT_CSV_PATH}")
                DataStore._df = pd.DataFrame()

        prediction_data_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'Predicted_Data.csv')
        should_reload_predictions = force_reload_predictions or DataStore._df_predictions is None

        # Auto-refresh when CSV is updated on disk.
        try:
            current_mtime = os.path.getmtime(prediction_data_path)
            if DataStore._predictions_mtime is None or current_mtime != DataStore._predictions_mtime:
                should_reload_predictions = True
        except FileNotFoundError:
            current_mtime = None

        if should_reload_predictions:
            try:
                DataStore._df_predictions = pd.read_csv(prediction_data_path)
                if 'student_id' in DataStore._df_predictions.columns:
                    DataStore._df_predictions['student_id'] = DataStore._df_predictions['student_id'].astype(str).str.strip()
                DataStore._predictions_mtime = current_mtime
                print(f"[INFO] DataStore: Successfully loaded {len(DataStore._df_predictions)} student predictions.")
            except FileNotFoundError:
                print(f"[ERROR] DataStore: Predicted_Data.csv not found at {prediction_data_path}")
                DataStore._df_predictions = pd.DataFrame()
                DataStore._predictions_mtime = None

    @staticmethod
    def get_df():
        DataStore.load_data()
        return DataStore._df

    @staticmethod
    def get_predictions_df():
        # Always check for file changes before returning cached predictions.
        DataStore.load_data()
        return DataStore._df_predictions

    @staticmethod
    def get_company_list():
        DataStore.load_data()
        return DataStore._company_list

    @staticmethod
    def resolve_alias(name):
        return DataStore._company_aliases.get(name.lower(), name)

# Initialize on import
DataStore.load_data()

# ==================== ENTITY RESOLVER ====================
# ==================== ENTITY RESOLVER ====================

ALIAS_MAP = {
    'micro': 'Microsoft',
    'ms': 'Microsoft',
    'goog': 'Google',
    'ggl': 'Google',
    'amzn': 'Amazon',
    'tcs': 'TCS',
    'infy': 'Infosys'
}

def _backlogs_allowed_count(val) -> int:
    """Convert backlogs_allowed to int (0 = not allowed, >0 = max backlogs).
    Handles both legacy True/False strings and new-style integer values."""
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return 1 if str(val).strip().lower() == 'true' else 0

def _extract_roles_text(row) -> str:
    roles_raw = str(row.get('hiring_roles_description', row.get('job_role_notes', 'Not specified')))
    return roles_raw.strip() if roles_raw.strip() else 'Not specified'

def _split_items(text: str) -> List[str]:
    if not text:
        return []
    cleaned = str(text).replace(';', ',').replace('|', ',')
    parts = [p.strip() for p in cleaned.split(',') if p.strip()]
    seen = set()
    out = []
    for p in parts:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out

def _extract_role_query(text: str) -> Optional[str]:
    raw = (text or '').lower()
    role_map = {
        'software engineer': ['software engineer', 'sde', 'developer'],
        'backend': ['backend'],
        'data engineer': ['data engineer', 'analytics', 'data'],
        'embedded': ['embedded'],
        'support': ['support'],
        'consulting': ['consulting'],
    }
    for role, keywords in role_map.items():
        if any(k in raw for k in keywords):
            return role
    return None

def resolve_company(tracker: Tracker) -> Tuple[Optional[Text], Optional[Text]]:
    """
    ENHANCED: Alias (Rule) -> Entity -> Fuzzy -> Context
    Returns: (company, match_source)
    """
    intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
    
    # Whitelist of intents allowed to use context (follow-ups)
    CONTEXT_ALLOWED_INTENTS = [
        'ask_avg_package', 'ask_max_package', 'ask_min_cgpa', 
        'ask_allowed_departments', 'ask_required_skills', 
        'ask_backlog_allowed', 'ask_max_backlogs', 'ask_company_backlogs',
        'ask_company_tier', 'ask_hiring_roles', 
        'ask_eligibility_summary', 'ask_interview_process', 'ask_round_duration',
        'ask_preparation_roadmap', 'ask_prep_topics_by_area'
    ]

    print(f"[DEBUG] RAW ENTITIES: {tracker.latest_message.get('entities', [])}")

    latest_entity = next(
        (e['value'] for e in tracker.latest_message.get('entities', []) 
         if e['entity'] == 'company'), 
        None
    )
    
    previous_company_slot = tracker.get_slot("company") # Added check for 'company' slot
    
    # Context check (Only if intent is in whitelist)
    # Priority: Context Slot > Company Slot
    last_company = tracker.get_slot("last_company_asked")
    if intent not in CONTEXT_ALLOWED_INTENTS:
        last_company = None
        previous_company_slot = None
    
    raw_text = tracker.latest_message.get('text', '')
    
    print(f"[DEBUG] Intent: {intent} | Entity: {latest_entity} | Context Allowed: {intent in CONTEXT_ALLOWED_INTENTS} | Last Context: {last_company} | Company Slot: {previous_company_slot}")
    
    company_list = DataStore.get_company_list()
    if not company_list:
        return None, None
    
    # Priority 0: Strict Alias Mapping (Rule-Based)
    alias_match = DataStore.resolve_alias(raw_text)
    if alias_match and alias_match != raw_text:
        print(f"[DEBUG] resolve_company | match_source: alias | match: {alias_match}")
        return alias_match, 'alias'
    
    # Priority 1: Use entity if available
    if latest_entity:
        target = latest_entity
        threshold = 60
        best_match, score = process.extractOne(target, company_list)
        if score >= threshold:
            print(f"[DEBUG] match_source: entity | score: {score} | match: {best_match}")
            return best_match, 'entity'
    
    # Priority 2: Fuzzy match on raw text (Only if intent implies a company query)
    IF_COMPANY_INTENT = latest_entity or intent in CONTEXT_ALLOWED_INTENTS or "topic" in raw_text.lower() or "eligible" in raw_text.lower()
    
    if IF_COMPANY_INTENT:
        target = raw_text
        # Lower threshold for raw text if keywords are present
        threshold = 70 if any(k in raw_text.lower() for k in ["topic", "prep", "eligible", "criteria"]) else 85
        best_match, score = process.extractOne(target, company_list)
        if score >= threshold:
            log_debug(f"[DEBUG] resolve_company | match_source: fuzzy | score: {score} | match: {best_match} | query: {target}")
            log_debug(f"[DEBUG] resolve_company | match_source: fuzzy | score: {score} | match: {best_match} | query: {target}")
            return best_match, 'fuzzy'
            
    # CRITICAL: If alias/fuzzy failed, DO NOT fallback to context if it's a completely new query 
    # that looks like a company name but failed validation.
    # But current logic only checks context if 'last_company' exists.
    
    # Priority 3: Use context if allowed
    
    # 3a. Use 'last_company_asked' (Immediate previous context)
    if last_company:
        log_debug(f"[DEBUG] resolve_company | match_source: context | value: {last_company}")
        return last_company, 'context'
        
    # 3b. Use 'company' slot (Holding state from 'inform_company')
    if previous_company_slot:
        log_debug(f"[DEBUG] resolve_company | match_source: slot_company | value: {previous_company_slot}")
        return previous_company_slot, 'context'
        
    log_debug(f"[DEBUG] resolve_company | No company resolved | Intent: {intent} | Text: {raw_text}")
    return None, None

# ==================== HUMAN-LIKE RESPONSE TEMPLATES ====================

def _tier_label(tier_val) -> str:
    t = str(tier_val).strip()
    if '1' in t:   return "Tier-1"
    if '2' in t:   return "Tier-2"
    if '3' in t:   return "Tier-3"
    return str(t)

def _difficulty_label(d) -> str:
    try:
        v = float(d)
        if v >= 8:   return "highly competitive"
        if v >= 6:   return "moderately competitive"
        return "relatively accessible"
    except Exception:
        return "competitive"

def _hiring_label(h) -> str:
    try:
        v = float(h)
        if v >= 8:   return "a mass recruiter hiring a large number of students"
        if v >= 5:   return "a selective recruiter that hires in moderate numbers"
        return "a niche recruiter that hires very selectively"
    except Exception:
        return "an active campus recruiter"

def _backlogs_sentence(row) -> str:
    max_bl = _backlogs_allowed_count(row['backlogs_allowed'])
    if max_bl == 0:
        return "No backlogs are allowed — candidates must have a clean academic record."
    return f"Students with up to {max_bl} active backlog(s) are allowed to apply."

# --- TEMPLATE 1: Company Overview ---
def tpl_company_overview(row) -> str:
    tier = _tier_label(row['company_tier'])
    roles = _extract_roles_text(row)
    skills = str(row.get('required_skills', 'Not specified'))
    return (
        f"Sure! Here's a quick overview of {row['company_name']}.\n\n"
        f"{row['company_name']} is categorized as a {tier} company in the dataset.\n\n"
        f"• Average Package: {row['avg_package_lpa']} LPA\n"
        f"• Maximum Package: {row['max_package_lpa']} LPA\n"
        f"• Minimum CGPA Required: {row['min_cgpa']}\n"
        f"• Allowed Departments: {row['allowed_departments']}\n"
        f"• Hiring Roles: {roles}\n\n"
        f"The company mainly looks for skills such as {skills}.\n\n"
        f"If you'd like, I can also explain the interview process or preparation topics for this company."
    )

# --- TEMPLATE 2: Eligibility ---
def tpl_eligibility(row) -> str:
    tier = _tier_label(row['company_tier'])
    if tier == "Tier-1":
        cgpa_note = "This is a premium company, so the CGPA bar is strict."
    elif tier == "Tier-2":
        cgpa_note = "This is reasonable for a mid-tier company."
    else:
        cgpa_note = "This is a relatively low bar, making it accessible to most students."
    return (
        f"To apply for {row['company_name']}, students need a minimum CGPA of {row['min_cgpa']}. "
        f"{cgpa_note}\n\n"
        f"Eligible departments include: {row['allowed_departments']}.\n\n"
        f"{_backlogs_sentence(row)}\n\n"
        f"Candidates should also have skills such as {row['required_skills']} to improve their chances."
    )

# --- TEMPLATE 3: Salary / Package ---
def tpl_salary(row) -> str:
    roles = _extract_roles_text(row)
    return (
        f"You asked about the average package offered by {row['company_name']}.\n\n"
        f"Based on the placement dataset, {row['company_name']} offers an average package of around {row['avg_package_lpa']} LPA.\n\n"
        f"This package typically reflects the salary offered to most students selected for roles like {roles}.\n\n"
        f"If you'd like, I can also tell you the maximum package offered by this company or explain their interview process."
    )

# --- TEMPLATE 4: Difficulty ---
def tpl_difficulty(row) -> str:
    d = float(row['difficulty_factor']) if str(row['difficulty_factor']).replace('.','').isdigit() else 5
    tier = _tier_label(row['company_tier'])
    if d >= 8:
        opening = f"Getting into {row['company_name']} is considered very tough."
    elif d >= 6:
        opening = f"Getting into {row['company_name']} requires solid preparation."
    else:
        opening = f"{row['company_name']} has a relatively accessible hiring process for well-prepared students."
    if tier == "Tier-1":
        tier_note = "As a Tier-1 company, the bar for technical skills is significantly higher."
    elif tier == "Tier-2":
        tier_note = "As a Tier-2 company, both technical and communication skills matter equally."
    else:
        tier_note = "As a Tier-3 company, aptitude and basics are weighted more heavily."
    return (
        f"{opening} The overall difficulty is rated {row['difficulty_factor']}/10.\n\n"
        f"{tier_note}\n\n"
        f"Here is how the company weights each area during recruitment:\n"
        f"  • DSA & Problem Solving : {row['weight_dsa']}\n"
        f"  • Project Experience    : {row['weight_projects']}\n"
        f"  • CS Fundamentals       : {row['weight_cs']}\n"
        f"  • Aptitude Tests        : {row['weight_aptitude']}\n"
        f"  • HR Interview          : {row['weight_hr']}\n\n"
        f"Focus on the highest-weighted areas to maximise your chances."
    )

# --- TEMPLATE 5: Skills ---
def tpl_skills(row) -> str:
    tier = _tier_label(row['company_tier'])
    if tier == "Tier-1":
        focus = "For a Tier-1 company like this, DSA and system design are the most critical areas."
    elif tier == "Tier-2":
        focus = "For a Tier-2 company, a balanced approach across DSA, CS fundamentals, and projects works best."
    else:
        focus = "For a Tier-3 company, aptitude tests and basic programming skills are usually sufficient to clear the initial rounds."
    return (
        f"To get selected at {row['company_name']}, you should develop the following skills:\n\n"
        f"Core required skills: {row['required_skills']}\n\n"
        f"{focus}\n\n"
        f"Recruitment area weights:\n"
        f"  • DSA                   : {row['weight_dsa']}\n"
        f"  • Project Experience    : {row['weight_projects']}\n"
        f"  • CS Fundamentals       : {row['weight_cs']}\n"
        f"  • Aptitude              : {row['weight_aptitude']}"
    )

# --- TEMPLATE 6: Departments ---
def tpl_departments(row) -> str:
    depts = str(row['allowed_departments'])
    tier = _tier_label(row['company_tier'])
    if tier == "Tier-1":
        note = "Most Tier-1 companies prefer students from CS/IT backgrounds due to their strong technical focus."
    else:
        note = "Students from related technical branches also stand a good chance if their skills are strong."
    return (
        f"Students from the following departments are eligible to apply for {row['company_name']}:\n"
        f"{depts}\n\n"
        f"{note}"
    )

# --- TEMPLATE 7: Backlog Policy ---
def tpl_backlog_policy(row) -> str:
    max_bl = _backlogs_allowed_count(row['backlogs_allowed'])
    tier = _tier_label(row['company_tier'])
    if max_bl == 0:
        verdict = f"{row['company_name']} has a strict no-backlog policy."
        advice = "You must clear all pending backlogs before applying."
    else:
        verdict = f"{row['company_name']} allows students with up to {max_bl} active backlog(s) to apply."
        advice = "However, clearing your backlogs improves your profile significantly."
    if tier == "Tier-1":
        tier_note = "Tier-1 companies are typically very strict about academic records."
    elif tier == "Tier-2":
        tier_note = "Tier-2 companies are somewhat flexible, but prefer a clean record."
    else:
        tier_note = "Tier-3 companies tend to be more lenient about backlogs during mass hiring."
    return f"{verdict} {tier_note}\n\n{advice}"

# --- TEMPLATE 8: Hiring Pattern ---
def tpl_hiring_pattern(row) -> str:
    return (
        f"{row['company_name']} is {_hiring_label(row['hiring_intensity'])}.\n\n"
        f"The hiring intensity is rated {row['hiring_intensity']}/10, which reflects how actively "
        f"the company participates in campus placements and how many students it typically selects.\n\n"
        f"This is a {row['company_cat']} company, which means its workforce requirements "
        f"are shaped by {'product development cycles' if 'product' in str(row['company_cat']).lower() else 'client project demands and service delivery'}."
    )

# --- TEMPLATE 9: Job Roles ---
def tpl_job_roles(row) -> str:
    roles = _split_items(_extract_roles_text(row))
    role_lines = "\n".join([f"• {r}" for r in roles[:5]]) if roles else "• Not specified"
    skills = str(row.get('required_skills', 'Not specified'))
    return (
        f"Sure! {row['company_name']} hires for roles such as:\n\n"
        f"{role_lines}\n\n"
        f"These roles usually involve working on areas described as: {_extract_roles_text(row)}.\n\n"
        f"To prepare for these roles, students generally need strong skills in {skills}.\n\n"
        f"If you're interested, I can also explain the interview rounds or preparation topics for these roles."
    )

# --- TEMPLATE 10: Category ---
def tpl_category(row) -> str:
    cat = str(row['company_cat'])
    if 'product' in cat.lower():
        desc = "primarily builds its own software products and platforms"
    elif 'service' in cat.lower():
        desc = "primarily delivers IT services to external clients"
    else:
        desc = "operates across both product and service verticals"
    return (
        f"{row['company_name']} is categorised as a {cat} company.\n\n"
        f"This means the company {desc}. "
        f"The type of work you do, the tech stack you use, and the growth trajectory "
        f"you can expect will all be influenced by this classification."
    )

# --- TEMPLATE 11: Tier ---
def tpl_tier(row) -> str:
    tier = _tier_label(row['company_tier'])
    return (
        f"You asked about the tier for {row['company_name']}.\n\n"
        f"According to the placement dataset, {row['company_name']} is categorized as {tier}.\n\n"
        f"Tier classification helps estimate expected package level and interview competitiveness.\n\n"
        f"If you'd like, I can also show this company's package details and eligibility criteria."
    )

# --- TEMPLATE 12: Preparation ---
def tpl_preparation(row) -> str:
    tier = _tier_label(row['company_tier'])
    if tier == "Tier-1":
        strategy = ("Focus heavily on DSA — practice 150+ problems on LeetCode. "
                    "Learn system design concepts and be ready for 4-5 interview rounds.")
    elif tier == "Tier-2":
        strategy = ("Balance your preparation between DSA, CS fundamentals (DBMS, OS, OOPS), "
                    "and one or two strong projects. Typically 2-3 interview rounds.")
    else:
        strategy = ("Focus on aptitude tests, basic programming, and verbal communication. "
                    "Tier-3 hiring often starts with an online test, followed by HR rounds.")
    return (
        f"To prepare for {row['company_name']}, here is what you should focus on:\n\n"
        f"Core skills: {row['required_skills']}\n\n"
        f"Preparation areas by weight:\n"
        f"  • DSA                   : {row['weight_dsa']}\n"
        f"  • CS Fundamentals       : {row['weight_cs']}\n"
        f"  • Project Experience    : {row['weight_projects']}\n"
        f"  • Aptitude              : {row['weight_aptitude']}\n"
        f"  • HR Interview          : {row['weight_hr']}\n\n"
        f"Strategy: {strategy}"
    )

# --- TEMPLATE 13: Suitability (requires student row too) ---
def tpl_suitability(student, row) -> str:
    cgpa_ok = float(student.get('cgpa', 0)) >= float(row['min_cgpa'])
    max_bl  = _backlogs_allowed_count(row['backlogs_allowed'])
    eligibility = "eligible" if cgpa_ok else "not currently eligible"
    if cgpa_ok:
        cgpa_msg = (f"Your CGPA of {student['cgpa']} meets the minimum requirement of {row['min_cgpa']}. "
                    f"That is a good start!")
    else:
        gap = round(float(row['min_cgpa']) - float(student.get('cgpa', 0)), 2)
        cgpa_msg = (f"Your CGPA of {student['cgpa']} is {gap} points below "
                    f"the required {row['min_cgpa']}.")
    return (
        f"Based on your academic profile, you are {eligibility} to apply for {row['company_name']}.\n\n"
        f"{cgpa_msg}\n\n"
        f"The company allows up to {max_bl} backlog(s).\n\n"
        f"To improve your chances, focus on strengthening: {row['required_skills']}."
    )

# --- TEMPLATE 14: Comparison (two company rows) ---
def tpl_comparison(r1, r2) -> str:
    pkg_winner  = r1['company_name'] if float(r1['avg_package_lpa']) >= float(r2['avg_package_lpa']) else r2['company_name']
    diff_easier = r1['company_name'] if float(r1['difficulty_factor']) <= float(r2['difficulty_factor']) else r2['company_name']
    cgpa_lower  = r1['company_name'] if float(r1['min_cgpa']) <= float(r2['min_cgpa']) else r2['company_name']
    return (
        f"Here is a comparison between {r1['company_name']} and {r2['company_name']}:\n\n"
        f"Average Package:\n"
        f"  • {r1['company_name']} : {r1['avg_package_lpa']} LPA\n"
        f"  • {r2['company_name']} : {r2['avg_package_lpa']} LPA\n"
        f"  → {pkg_winner} offers a higher average salary.\n\n"
        f"Difficulty Level:\n"
        f"  • {r1['company_name']} : {r1['difficulty_factor']}/10\n"
        f"  • {r2['company_name']} : {r2['difficulty_factor']}/10\n"
        f"  → {diff_easier} has a relatively easier selection process.\n\n"
        f"Minimum CGPA:\n"
        f"  • {r1['company_name']} : {r1['min_cgpa']}\n"
        f"  • {r2['company_name']} : {r2['min_cgpa']}\n"
        f"  → {cgpa_lower} has a lower CGPA requirement."
    )

# ==================== LAYER 1: COMPANY-SPECIFIC ACTIONS ====================

class ActionGetAvgPackage(Action):
    def name(self) -> Text:
        return "action_get_avg_package"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's average package? (e.g., 'Google average package')")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            response = tpl_salary(row)
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Average package data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetMaxPackage(Action):
    def name(self) -> Text:
        return "action_get_max_package"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's maximum package?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            response = (
                f"You asked about the maximum package offered by {company}.\n\n"
                f"According to the dataset, the highest package offered by {company} is around {row['max_package_lpa']} LPA.\n\n"
                "This is usually offered to candidates who perform exceptionally well in the interview rounds or secure higher-level technical roles.\n\n"
                "If you'd like, I can also show you how this compares with other companies."
            )
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Maximum package data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetMinCGPA(Action):
    def name(self) -> Text:
        return "action_get_min_cgpa"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's CGPA requirement?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            val = row['min_cgpa']
            response = (
                f"You asked about the minimum CGPA required for {company}.\n\n"
                f"According to the placement dataset, the minimum CGPA required to apply for {company} is {val}.\n\n"
                "Students who meet this CGPA requirement and also have strong skills in areas like data structures, algorithms, and programming generally have a better chance of clearing the selection process.\n\n"
                "If you'd like, I can also explain the interview rounds or preparation topics for this company."
            )
            print(f"[DEBUG] Action: {self.name()} | Company: {company} | CGPA: {val}")
        except IndexError:
            response = f"CGPA data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetAllowedDepartments(Action):
    def name(self) -> Text:
        return "action_get_allowed_departments"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's branch eligibility?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            allowed = _split_items(str(row.get('allowed_departments', '')))
            user_text = tracker.latest_message.get('text', '').lower()

            dept_aliases = {
                'cse': ['cse', 'computer science'],
                'it': ['it', 'information technology'],
                'ece': ['ece', 'electronics'],
                'ee': ['ee', 'electrical'],
                'ai': ['ai', 'artificial intelligence'],
                'ds': ['ds', 'data science'],
            }
            asked_dept = None
            for canonical, keys in dept_aliases.items():
                if any(k in user_text for k in keys):
                    asked_dept = canonical
                    break

            if asked_dept:
                is_allowed = any(asked_dept in a.lower() for a in allowed)
                response = (
                    f"You asked whether {asked_dept.upper()} students can apply for {company}.\n\n"
                    f"According to the dataset, the allowed departments for this company include: {', '.join(allowed) if allowed else 'Not specified'}.\n\n"
                    + ("If your department is listed above, you are eligible to apply for this company." if is_allowed else "Your department is not listed in the allowed departments for this company in the current dataset.")
                    + "\n\nIf you'd like, I can also help you find companies that accept your department."
                )
            else:
                response = (
                    f"You asked which departments are eligible for {company}.\n\n"
                    "According to the placement dataset, the following departments can apply:\n\n"
                    + "\n".join([f"• {d}" for d in allowed])
                    + "\n\nStudents from these departments are eligible as long as they meet the CGPA and other eligibility criteria.\n\n"
                    "If you'd like, I can also tell you the skills required for this company."
                )
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Branch eligibility data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetRequiredSkills(Action):
    def name(self) -> Text:
        return "action_get_required_skills"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's skill requirements?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            response = tpl_skills(row)
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Skill data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetCompanyBacklogPolicy(Action):
    def name(self) -> Text:
        return "action_get_company_backlog_policy"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's backlog policy?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
            response = tpl_backlog_policy(row)
                
        except IndexError:
            response = f"Backlog policy not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetCompanyTier(Action):
    def name(self) -> Text:
        return "action_get_company_tier"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's tier?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            response = tpl_tier(row)
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Tier data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetHiringRoles(Action):
    def name(self) -> Text:
        return "action_get_hiring_roles"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker) # FIXED: Resolve company first
        df = DataStore.get_df()

        # Support role-based query: "Which companies hire Software Engineers?"
        if not company:
            role_query = _extract_role_query(tracker.latest_message.get('text', ''))
            if role_query:
                matching = df[df['hiring_roles_description'].astype(str).str.lower().str.contains(role_query, na=False)]
                companies = matching['company_name'].tolist()
                if companies:
                    sample_skills = ", ".join(_split_items(str(matching.iloc[0].get('required_skills', '')))[0:3])
                    response = (
                        f"Several companies in the dataset hire for the role of {role_query.title()}.\n\n"
                        "Some of the companies include:\n"
                        + "\n".join([f"• {c}" for c in companies[:10]])
                        + f"\n\nThese companies typically look for strong skills in areas like {sample_skills if sample_skills else 'data structures, algorithms, and programming fundamentals'}.\n\n"
                        "If you want, I can also show you which of these companies offer the highest packages or have easier eligibility criteria."
                    )
                else:
                    response = f"I could not find companies explicitly hiring for {role_query.title()} in the current dataset."
                dispatcher.utter_message(text=response)
                return [SlotSet("company", None), SlotSet("last_company_asked", None)]

        if not company:
            dispatcher.utter_message(text="Which company's hiring roles?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]

        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            response = tpl_job_roles(row)
            print(f"[DEBUG] Action: {self.name()} | Company: {company}")
        except IndexError:
            response = f"Hiring roles data not available for {company}."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetEligibilitySummary(Action):
    def name(self) -> Text:
        return "action_get_eligibility_summary"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's eligibility criteria?")
            return [SlotSet("company_name", None)]
        
        print(f"[ACTION] {self.name()} | Resolved Company: {company}")
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            print(f"[ACTION] {self.name()} | CSV Row Index: {row_index}")
            response = tpl_eligibility(row)
        except IndexError:
            print(f"[ACTION] {self.name()} | ERROR: Company not found in CSV")
            response = f"Eligibility data not available for {company}."
        
        dispatcher.utter_message(text=response)
        events = [SlotSet("company", None)]
        if source in ['entity', 'fuzzy', 'alias']:
            events.append(SlotSet("last_company_asked", company))
        else:
            events.append(SlotSet("last_company_asked", None))
        return events

class ActionCheckEligibility(Action):
    def name(self) -> Text:
        return "action_check_eligibility"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        
        if not company:
             dispatcher.utter_message(text="Which company's eligibility do you want to check?")
             return [SlotSet("company_name", None)]
        
        text = tracker.latest_message.get('text', '')
        import re
        
        # Regex for text-based extraction
        cgpa_pattern = r'(\d+(?:\.\d+)?)\s*(?:cgpa|pointer|cp|gpa)'
        backlog_pattern = r'(\d+)\s*(?:backlogs?|active backlogs?)'
        
        cgpa_match = re.search(cgpa_pattern, text, re.IGNORECASE)
        backlog_match = re.search(backlog_pattern, text, re.IGNORECASE)
        
        user_cgpa = float(cgpa_match.group(1)) if cgpa_match else None
        user_backlogs = int(backlog_match.group(1)) if backlog_match else 0
        
        if user_cgpa is None:
             dispatcher.utter_message(text=f"Please specify your CGPA to check eligibility for {company}. (e.g. 'I have 8.5 CGPA')")
             return [SlotSet("company", None), SlotSet("last_company_asked", company)]
             
        df = DataStore.get_df()
        try:
             row_index = df[df['company_name'] == company].index[0]
             row = df.iloc[row_index]
             
             min_cgpa = float(row['min_cgpa'])
             max_backlogs = _backlogs_allowed_count(row['backlogs_allowed'])
             backlogs_allowed = max_backlogs > 0
             
             cgpa_ok = user_cgpa >= min_cgpa
             backlog_ok = (user_backlogs <= max_backlogs) if backlogs_allowed else (user_backlogs == 0)
            
             is_eligible = cgpa_ok and backlog_ok
             status_icon = "✅ Eligible" if is_eligible else "❌ Not Eligible"
             cgpa_sym = "✔" if cgpa_ok else "❌"
             backlog_sym = "✔" if backlog_ok else "❌"
             
             print(f"[DEBUG] Action: {self.name()} | Company: {company} | CGPA: {user_cgpa} vs {min_cgpa} | Backlogs: {user_backlogs} vs {max_backlogs}")

             response = (
                 f"🎯 Eligibility Assessment for {company}:\n\n"
                 f"{cgpa_sym} CGPA: {user_cgpa} (Min required: {min_cgpa})\n"
                 f"{backlog_sym} Backlogs: {user_backlogs} (Max allowed: {max_backlogs if backlogs_allowed else 0})\n\n"
                 f"📢 Result: You are {status_icon} for {company}."
             )
             dispatcher.utter_message(text=response)
             
        except Exception as e:
             print(f"[ACTION] {self.name()} | ERROR: {str(e)}")
             dispatcher.utter_message(text="Data not available for this company.")

        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionGetInterviewProcess(Action):
    def name(self) -> Text:
        return "action_get_interview_process"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker) # Fixed: Resolve company first!

        if not company:
            dispatcher.utter_message(text="Which company's interview process? (e.g., 'Amazon interview rounds')")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            
            round_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            rounds = []
            
            for i in range(1, 5): 
                name = row.get(f'round{i}_name', '')
                if pd.isna(name) or not str(name).strip(): continue
                
                duration = row.get(f'round{i}_duration_min', 'N/A')
                focus = row.get(f'round{i}_focus', 'General')
                rounds.append(f"{round_emojis[i-1]} **{name}**\n   ⏱ Duration: {duration} mins\n   🎯 Focus: {focus}")

            print(f"[DEBUG] Action: {self.name()} | Company: {company} | Rounds Found: {len(rounds)}")

            if rounds:
                response = f"⚔️ Interview Process for {company}:\n\n" + "\n\n".join(rounds)
            else:
                response = "Data not available for this company."
        
        except IndexError:
            response = "Data not available for this company."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]

class ActionPrepTopicsByArea(Action):
    def name(self) -> Text:
        return "action_prep_topics_by_area"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        
        # Check if it's a general HR query without company/area mentioned specifically
        # (Though rules should handle ask_general_hr_question, this is safety)
        if intent == 'ask_general_hr_question':
            return []

        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's specific topics? (e.g., 'Google dbms topics')")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
            
        prep_area = next((e['value'] for e in tracker.latest_message.get('entities', []) if e['entity'] == 'prep_area'), None)
        
        # STRICT MANDATORY MAPPING
        AREA_TO_COLUMN = {
            'dsa': 'prep_dsa_topics',
            'dbms': 'prep_dbms_topics',
            'oops': 'prep_oops_topics',
            'system_design': 'prep_system_design_topics',
            'hr': 'prep_hr_topics'
        }
        
        target_col = AREA_TO_COLUMN.get(prep_area.lower()) if prep_area else None
            
        if not target_col:
             dispatcher.utter_message(text=f"Please specify a valid topic area (DSA, DBMS, OOPS, System Design, HR) for {company}.")
             return [SlotSet("company", None), SlotSet("last_company_asked", None)]

        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            
            # DIAGNOSTIC LOGGING
            log_debug(f"[DIAGNOSTIC] Company: {company} | Target Column: {target_col}")
            log_debug(f"[DIAGNOSTIC] Columns in DF: {df.columns.tolist()}")
            
            topic_content = row.get(target_col, '')
            log_debug(f"[DEBUG] Action: {self.name()} | Content: {topic_content}")

            if pd.isna(topic_content) or str(topic_content).upper() == 'NA' or not str(topic_content).strip():
                 response = "Data not available for this company."
            else:
                 formatted_area = prep_area.replace('_', ' ').upper()
                 response = f"{formatted_area} Topics for {company}:\n- {topic_content}"
                 
            dispatcher.utter_message(text=response)
            
        except IndexError:
             dispatcher.utter_message(text=f"Company {company} not found.")
             
        # STRICT SLOT RESET POLICY: Reset prep_area to prevent loop
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None), SlotSet("prep_area", None)]

class ActionGetPreparationRoadmap(Action):
    def name(self) -> Text:
        return "action_get_preparation_roadmap"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Hard Fix for Loop: If user explicitly says "full", ignore prep_area slot artifact
        raw_text = tracker.latest_message.get('text', '').lower()
        explicit_full = any(w in raw_text for w in ["full", "complete", "entire", "whole", "all"])

        # HARD BLOCK as per TC-22 Requirement (Only if NOT explicitly asking for full)
        if tracker.get_slot("prep_area") and not explicit_full:
            dispatcher.utter_message(
                text="Please specify if you want the full study roadmap or only a specific topic."
            )
            return []

        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        print(f"[ACTION] {self.name()} | Intent: {intent}")
        
        company, source = resolve_company(tracker) # FIXED: Resolve company first

        if not company:
            dispatcher.utter_message(text="Which company's preparation roadmap? (e.g., 'Google preparation topics')")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        df = DataStore.get_df()
        try:
            row_index = df[df['company_name'] == company].index[0]
            row = df.iloc[row_index]
            
            prep_sections = []
            
            # 1. Technical Areas (Dynamic Mapping)
            AREA_TO_LABEL = {
                'prep_dsa_topics': 'DSA',
                'prep_system_design_topics': 'System Design',
                'prep_oops_topics': 'OOPS',
                'prep_dbms_topics': 'DBMS',
                'prep_hr_topics': 'HR'
            }
            
            for col, label in AREA_TO_LABEL.items():
                val = row.get(col, '')
                if pd.notna(val) and str(val).strip() and str(val).upper() != 'NA':
                    prep_sections.append(f"🔹 {label}:\n- {val}")
            
            print(f"[DEBUG] Action: {self.name()} | Company: {company} | Prep Sections: {len(prep_sections)}")

            if prep_sections:
                response = f"📘 Full Preparation Roadmap for {company}:\n\n" + "\n\n".join(prep_sections)
            else:
                # Fallback: detailed topic columns not in CSV, use human-like preparation template
                response = tpl_preparation(row)
        
        except IndexError:
            response = "Data not available for this company."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


# -------------------- NEW HUMAN-LIKE LAYER 1 ACTIONS --------------------

class ActionGetCompanyOverview(Action):
    def name(self) -> Text:
        return "action_get_company_overview"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's overview would you like?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_company_overview(row)
        except IndexError:
            response = f"Overview not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetCompanyDifficulty(Action):
    def name(self) -> Text:
        return "action_get_company_difficulty"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's difficulty level?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_difficulty(row)
        except IndexError:
            response = f"Difficulty data not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetHiringPattern(Action):
    def name(self) -> Text:
        return "action_get_hiring_pattern"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's hiring pattern?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_hiring_pattern(row)
        except IndexError:
            response = f"Hiring pattern data not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetJobRoles(Action):
    def name(self) -> Text:
        return "action_get_job_roles"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's job roles?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_job_roles(row)
        except IndexError:
            response = f"Job role data not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetCompanyCategory(Action):
    def name(self) -> Text:
        return "action_get_company_category"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's category?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_category(row)
        except IndexError:
            response = f"Category data not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetCompanyTierInfo(Action):
    def name(self) -> Text:
        return "action_get_company_tier_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's tier information?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_tier(row)
        except IndexError:
            response = f"Tier info not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionGetCompanyPreparation(Action):
    def name(self) -> Text:
        return "action_get_company_preparation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        company, source = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's preparation guide?")
            return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        df = DataStore.get_df()
        try:
            row = df[df['company_name'] == company].iloc[0]
            response = tpl_preparation(row)
        except IndexError:
            response = f"Preparation guide not available for {company}."
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", company if source in ['entity', 'fuzzy', 'alias'] else None)]


class ActionCompareCompanies(Action):
    def name(self) -> Text:
        return "action_compare_companies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entities = [e['value'] for e in tracker.latest_message.get('entities', []) if e['entity'] == 'company']
        df = DataStore.get_df()

        if len(entities) < 2:
            dispatcher.utter_message(text="Please name two companies to compare. (e.g., 'Compare Google and Infosys')")
            return [SlotSet("company", None)]

        try:
            from fuzzywuzzy import process as fwp
            company_list = df['company_name'].tolist()
            name1 = fwp.extractOne(entities[0], company_list)[0]
            name2 = fwp.extractOne(entities[1], company_list)[0]
            row1 = df[df['company_name'] == name1].iloc[0]
            row2 = df[df['company_name'] == name2].iloc[0]
            response = tpl_comparison(row1, row2)
        except Exception as e:
            print(f"[ERROR] ActionCompareCompanies: {e}")
            response = "Could not compare those companies. Please check the company names and try again."

        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", None)]


# ==================== LAYER 2: AGGREGATE ACTIONS ====================

class ActionListCompaniesByCGPA(Action):
    def name(self) -> Text:
        return "action_list_companies_by_cgpa"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()
        
        import re
        cgpa_match = re.search(r'(\d+\.?\d*)', user_text)
        cgpa_threshold = float(cgpa_match.group(1)) if cgpa_match else 7.0
        
        if 'highest cgpa' in user_text or 'strictest cgpa' in user_text:
            strict = df.sort_values('min_cgpa', ascending=False)[['company_name', 'min_cgpa']].values.tolist()
            response = (
                "You asked which companies have the highest CGPA requirement.\n\n"
                "Based on the placement dataset, the companies with the strictest CGPA eligibility include:\n\n"
                + "\n".join([f"• {c[0]} – Minimum CGPA: {c[1]}" for c in strict[:8]])
                + "\n\nThese companies usually belong to higher placement tiers and have competitive hiring processes.\n\n"
                "If you'd like, I can also show you companies with lower CGPA requirements."
            )
            dispatcher.utter_message(text=response)
            return []
        elif 'lowest' in user_text or 'low cgpa' in user_text or 'easy cgpa' in user_text or 'minimum requirement' in user_text:
            sorted_df = df.sort_values('min_cgpa', ascending=True)
            companies_data = sorted_df[['company_name', 'min_cgpa']].values.tolist()
            companies = [c[0] for c in companies_data]
            response = (
                "You asked which companies are open to students with lower CGPA requirements.\n\n"
                "From the placement dataset, the companies with relatively flexible CGPA eligibility include:\n\n"
                + "\n".join([f"• {c[0]} – Minimum CGPA: {c[1]}" for c in companies_data[:12]])
                + "\n\nThese companies usually focus more on technical skills and interview performance rather than only CGPA.\n\n"
                "If you'd like, I can also show you how to prepare for these companies."
            )
        elif 'above' in user_text or 'more than' in user_text or 'greater' in user_text:
            filtered = df[df['min_cgpa'] <= cgpa_threshold]
            companies = filtered['company_name'].tolist()
            details = filtered[['company_name', 'min_cgpa']].sort_values('min_cgpa', ascending=False).values.tolist()
            response = (
                f"You asked which companies allow students with a CGPA above {cgpa_threshold}.\n\n"
                "Based on the placement dataset, the companies that you may be eligible for include:\n\n"
                + "\n".join([f"• {c[0]} – Minimum CGPA requirement: {c[1]}" for c in details[:15]])
                + "\n\nThese companies accept students whose CGPA meets or exceeds their minimum eligibility criteria.\n\n"
                "If you'd like, I can also help you find the companies offering the highest packages among these."
            )
        elif 'below' in user_text or 'less than' in user_text:
            filtered = df[df['min_cgpa'] >= cgpa_threshold]
            companies = filtered['company_name'].tolist()
            response = f"Companies requiring CGPA at least {cgpa_threshold}:\n" + "\n".join([f"- {c}" for c in companies[:15]])
        else:
            filtered = df[df['min_cgpa'] <= cgpa_threshold]
            companies = filtered['company_name'].tolist()
            response = f"Companies for CGPA {cgpa_threshold}:\n" + "\n".join([f"- {c}" for c in companies[:15]])
        
        if not companies:
            response = f"No companies found for CGPA {cgpa_threshold}."
        
        dispatcher.utter_message(text=response)
        return []

class ActionListCompaniesAllowingBacklogs(Action):
    def name(self) -> Text:
        return "action_list_companies_allowing_backlogs"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        filtered = df[df['backlogs_allowed'].apply(_backlogs_allowed_count) > 0]
        companies = filtered['company_name'].tolist()
        user_text = tracker.latest_message.get('text', '').lower()
        
        # String-based detection: count vs list
        count_keywords = ['how many', 'count', 'total', 'number of']
        is_count_query = any(keyword in user_text for keyword in count_keywords)

        # Student backlog eligibility check: "Can I apply with 1 backlog?"
        import re
        backlog_match = re.search(r'(\d+)\s*backlog', user_text)
        if backlog_match:
            b = int(backlog_match.group(1))
            match_df = df[df['backlogs_allowed'].apply(_backlogs_allowed_count) >= b]
            match_companies = match_df['company_name'].tolist()
            if match_companies:
                response = (
                    f"You asked whether you can apply with {b} backlog(s).\n\n"
                    "Companies that allow this backlog count include:\n\n"
                    + "\n".join([f"• {c}" for c in match_companies[:15]])
                    + "\n\nYou may still be eligible for these companies as long as your backlog count is within their allowed limit.\n\n"
                    "If you'd like, I can also help you find companies that match your CGPA and department eligibility."
                )
            else:
                response = f"I could not find companies allowing {b} backlog(s) in the current dataset."
            dispatcher.utter_message(text=response)
            return []
        
        if is_count_query:
            response = f"Total companies allowing backlogs: {len(companies)}"
        else:
            if companies:
                details = filtered[['company_name', 'backlogs_allowed']].values.tolist()
                response = (
                    "You asked which companies allow students with existing backlogs.\n\n"
                    "Based on the placement dataset, the companies that allow backlogs include:\n\n"
                    + "\n".join([f"• {c[0]} – Maximum allowed: {int(c[1])}" for c in details[:15]])
                    + "\n\nThese companies are relatively more flexible in their eligibility criteria.\n\n"
                    "If you'd like, I can also help you identify companies that match your CGPA and department."
                )
            else:
                response = "No companies found that allow backlogs."
        
        dispatcher.utter_message(text=response)
        return []

class ActionCountCompanies(Action):
    def name(self) -> Text:
        return "action_count_companies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()
        
        print(f"[DEBUG] Action: {self.name()} | Query: {user_text}")

        if 'backlog' in user_text:
            count = len(df[df['backlogs_allowed'].apply(_backlogs_allowed_count) > 0])
            response = f"Total companies allowing backlogs: {count}"
        elif 'tier-1' in user_text or 'tier 1' in user_text:
            count = len(df[df['company_tier'].str.contains('Tier-1', case=False, na=False)])
            response = f"There are {count} Tier-1 companies in our database."
        elif 'cgpa' in user_text:
            import re
            cgpa_match = re.search(r'(\d+\.?\d*)', user_text)
            cgpa = float(cgpa_match.group(1)) if cgpa_match else 7.0
            count = len(df[df['min_cgpa'] <= cgpa])
            response = f"There are {count} companies accepting CGPA {cgpa} or above."
        else:
            response = f"Currently, we have information for {len(df)} companies."
        
        dispatcher.utter_message(text=response)
        return [SlotSet("company", None), SlotSet("last_company_asked", None)]

class ActionListTier1Companies(Action):
    def name(self) -> Text:
        return "action_list_tier1_companies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()

        # Handle "all companies" / "campus visit" queries before tier filtering
        if any(k in user_text for k in ['visit', 'campus', 'all companies', 'every company', 'which companies']):
            all_companies = df['company_name'].tolist()
            preview = ", ".join(all_companies[:10])
            response = (
                "Here are the companies currently available in the placement dataset:\n\n"
                f"{preview}{', ...' if len(all_companies) > 10 else ''}\n\n"
                "These companies belong to different tiers and offer roles in areas like software development, data engineering, and other technical positions.\n\n"
                "If you'd like, I can also help you:\n"
                "• see which companies offer the highest packages\n"
                "• check eligibility criteria\n"
                "• compare companies\n\n"
                "Just tell me what you'd like to know."
            )
            dispatcher.utter_message(text=response)
            return []

        # Extract tier number (1, 2, or 3)
        tier = None
        if 'tier 1' in user_text or 'tier-1' in user_text or 'tier1' in user_text:
            tier = 'Tier-1'
        elif 'tier 2' in user_text or 'tier-2' in user_text or 'tier2' in user_text:
            tier = 'Tier-2'
        elif 'tier 3' in user_text or 'tier-3' in user_text or 'tier3' in user_text:
            tier = 'Tier-3'
        else:
            # Default to Tier-1 if no tier specified
            tier = 'Tier-1'
        
        # Filter by tier
        filtered = df[df['company_tier'].str.contains(tier, case=False, na=False)]
        companies = filtered['company_name'].tolist()
        
        # String-based detection: count vs list
        count_keywords = ['how many', 'count', 'total', 'number of']
        is_count_query = any(keyword in user_text for keyword in count_keywords)
        
        if is_count_query:
            # Return count only
            response = f"Total {tier} companies: {len(companies)}"
        else:
            # Return list
            if companies:
                response = (
                    f"The following companies are categorized as {tier} companies in the dataset:\n\n"
                    + ", ".join(companies)
                    + f"\n\n{tier} companies usually offer {'higher' if tier == 'Tier-1' else 'competitive'} salary packages and have a more competitive selection process compared to lower tiers.\n\n"
                    "If you'd like, I can also show you the packages or eligibility criteria for these companies."
                )
            else:
                response = f"No {tier} companies found."
        
        dispatcher.utter_message(text=response)
        return []

class ActionListHighPayingCompanies(Action):
    def name(self) -> Text:
        return "action_list_high_paying_companies"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()
        
        import re
        # Highest package / lowest package / threshold / range all handled here.
        if any(k in user_text for k in ['highest max package', 'highest package company']):
            row = df.sort_values('max_package_lpa', ascending=False).iloc[0]
            response = (
                "You asked which company offers the highest maximum package.\n\n"
                f"According to the placement dataset, {row['company_name']} currently offers the highest maximum package, reaching up to {row['max_package_lpa']} LPA.\n\n"
                "This makes it one of the most competitive companies in the placement list.\n\n"
                "If you'd like, I can also show you the companies that come next in terms of package."
            )
        elif any(k in user_text for k in ['highest salary', 'top salary', 'highest package']) and 'which company has' not in user_text:
            top = df.sort_values('max_package_lpa', ascending=False)[['company_name', 'max_package_lpa']].head(5).values.tolist()
            response = (
                "You asked which companies offer the highest salary packages.\n\n"
                "From the placement dataset, the companies with the top salary packages include:\n\n"
                + "\n".join([f"• {c[0]} – up to {c[1]} LPA" for c in top])
                + "\n\nThese companies typically fall into Tier 1 and usually have a more competitive selection process.\n\n"
                "If you're interested, I can also show you the eligibility criteria or interview rounds for these companies."
            )
        elif any(k in user_text for k in ['lowest package', 'lowest salary']):
            low = df.sort_values('avg_package_lpa', ascending=True)[['company_name', 'avg_package_lpa']].head(5).values.tolist()
            response = (
                "You asked which companies offer the lowest salary packages in the dataset.\n\n"
                "Based on the available data, the companies with comparatively lower packages include:\n\n"
                + "\n".join([f"• {c[0]} – around {c[1]} LPA" for c in low])
                + "\n\nThese companies often belong to Tier 3 or entry-level hiring categories, but they can still be good opportunities to start your career.\n\n"
                "If you'd like, I can also show you companies that offer higher packages."
            )
        else:
            # Range query: "between 10 and 20"
            range_match = re.search(r'between\s*(\d+(?:\.\d+)?)\s*and\s*(\d+(?:\.\d+)?)', user_text)
            if range_match:
                low_v = float(range_match.group(1))
                high_v = float(range_match.group(2))
                filtered = df[(df['avg_package_lpa'] >= low_v) & (df['avg_package_lpa'] <= high_v)].sort_values('avg_package_lpa', ascending=False)
                items = filtered[['company_name', 'avg_package_lpa']].values.tolist()
                if items:
                    response = (
                        f"You asked which companies offer packages between {low_v:.0f} and {high_v:.0f} LPA.\n\n"
                        "From the placement dataset, the companies that fall within this salary range include:\n\n"
                        + "\n".join([f"• {c[0]} – Average package around {c[1]} LPA" for c in items[:12]])
                        + "\n\nThese companies usually provide good opportunities for students entering technical roles.\n\n"
                        "If you'd like, I can also help you compare these companies based on eligibility or interview difficulty."
                    )
                else:
                    response = f"I could not find companies with average package between {low_v:.0f} and {high_v:.0f} LPA."
            else:
                package_match = re.search(r'(\d+(?:\.\d+)?)', user_text)
                threshold = float(package_match.group(1)) if package_match else 10.0
                filtered = df[df['avg_package_lpa'] >= threshold].sort_values('avg_package_lpa', ascending=False)
                items = filtered[['company_name', 'avg_package_lpa']].values.tolist()
                if items:
                    response = (
                        f"You asked which companies offer an average package higher than {threshold:.0f} LPA.\n\n"
                        "According to the placement dataset, the companies that meet this criteria include:\n\n"
                        + "\n".join([f"• {c[0]} – Average package around {c[1]} LPA" for c in items[:12]])
                        + "\n\nThese companies usually belong to higher placement tiers and have a competitive selection process.\n\n"
                        "If you'd like, I can also show you the preparation topics required for these companies."
                    )
                else:
                    response = f"No companies found offering more than {threshold:.0f} LPA average package."

        dispatcher.utter_message(text=response)
        return []


def _round_count_from_row(row) -> int:
    count = 0
    for i in range(1, 5):
        v = row.get(f'round{i}_name', '')
        if pd.notna(v) and str(v).strip():
            count += 1
    return count


def _resolve_two_companies(df: pd.DataFrame, tracker: Tracker, text: str) -> List[str]:
    entities = [e['value'] for e in tracker.latest_message.get('entities', []) if e.get('entity') == 'company']
    names: List[str] = []
    company_list = df['company_name'].tolist()

    if len(entities) >= 2:
        for e in entities[:2]:
            try:
                match = process.extractOne(e, company_list)
                if match:
                    names.append(match[0])
            except Exception:
                continue
        if len(names) >= 2:
            return names[:2]

    # Fallback: detect known company names present in raw text.
    found = []
    low = (text or '').lower()
    for c in company_list:
        if str(c).lower() in low:
            found.append(c)
    if len(found) >= 2:
        return found[:2]

    # Fallback for "A or B" pattern using fuzzy split.
    parts = re.split(r'\bor\b|\band\b|,', low)
    cand = [p.strip() for p in parts if p.strip()]
    for p in cand:
        try:
            match = process.extractOne(p, company_list)
            if match and match[1] >= 80 and match[0] not in names:
                names.append(match[0])
        except Exception:
            continue
        if len(names) >= 2:
            break
    return names[:2]


def _extract_number(text: str, default: float) -> float:
    m = re.search(r'(\d+(?:\.\d+)?)', text or '')
    return float(m.group(1)) if m else default


def _extract_top_n(text: str, default: int = 5) -> int:
    m = re.search(r'(?:top\s+)?(\d+)', (text or '').lower())
    if not m:
        return default
    try:
        return max(1, min(20, int(m.group(1))))
    except Exception:
        return default


def _safe_slug(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', str(value or '').lower()).strip('-')


def _list_leetcode_companies() -> List[str]:
    if not os.path.isdir(LEETCODE_DATA_DIR):
        return []
    names: List[str] = []
    for entry in os.listdir(LEETCODE_DATA_DIR):
        full_path = os.path.join(LEETCODE_DATA_DIR, entry)
        if os.path.isdir(full_path) and not entry.startswith('.'):
            names.append(entry)
    return sorted(names)


def _resolve_leetcode_company(tracker: Tracker, text: str, companies: List[str]) -> Optional[str]:
    if not companies:
        return None

    entity_candidates = [
        str(e.get('value', '')).strip()
        for e in tracker.latest_message.get('entities', [])
        if e.get('entity') == 'company'
    ]

    alias_map = {
        'fb': 'meta',
        'facebook': 'meta',
        'google llc': 'google',
        'amazon web services': 'amazon',
        'microsoft corporation': 'microsoft',
    }

    def _match_company(candidate: str) -> Optional[str]:
        c = candidate.strip().lower()
        if not c:
            return None
        if c in alias_map:
            c = alias_map[c]
        if c in companies:
            return c
        for company in companies:
            if company in c or c in company:
                return company
        best_match = process.extractOne(c, companies)
        if best_match and best_match[1] >= 78:
            return best_match[0]
        return None

    for entity in entity_candidates:
        matched = _match_company(entity)
        if matched:
            return matched

    text_low = (text or '').lower()
    for company in companies:
        if re.search(rf'\b{re.escape(company)}\b', text_low):
            return company

    best_from_text = process.extractOne(text_low, companies)
    if best_from_text and best_from_text[1] >= 82:
        return best_from_text[0]

    return None


def _resolve_leetcode_time_file(text: str) -> Tuple[str, str]:
    q = (text or '').lower()

    if any(k in q for k in ['newest', 'latest', 'recent', 'this month', 'latest month']):
        return 'thirty-days.csv', 'Last 30 Days'

    if any(k in q for k in ['30 day', '30 days', 'one month', '1 month']):
        return 'thirty-days.csv', 'Last 30 Days'

    if any(k in q for k in ['3 month', '3 months', 'three month', 'three months', 'quarter']):
        return 'three-months.csv', 'Last 3 Months'

    if any(k in q for k in ['6 month', '6 months', 'six month', 'six months', 'half year']):
        return 'six-months.csv', 'Last 6 Months'

    if any(k in q for k in ['1 year', 'one year', '12 month', '12 months', 'last year', 'past year']):
        # Dataset does not currently include a dedicated 1-year file; use best available aggregate.
        return 'all.csv', 'Last 1 Year (using available dataset)'

    if any(k in q for k in ['more than six months', 'older than six months', 'older', 'old questions']):
        return 'more-than-six-months.csv', 'More Than 6 Months'

    if any(k in q for k in ['all time', 'all questions', 'complete list', 'entire list']):
        return 'all.csv', 'All Time'

    # Default requirement: when no time is mentioned, use all.csv
    return 'all.csv', 'All Time'


def _is_leetcode_company_questions_query(tracker: Tracker, text: str, companies: List[str]) -> bool:
    q = (text or '').lower()
    if not q:
        return False

    # Fast-path explicit phrases.
    explicit_markers = [
        'leetcode', 'companywise questions', 'interview questions for',
        'questions asked by', 'questions from', 'problems asked by',
        'coding questions', 'interview problems', 'practice for',
        'preparation list', 'top interview questions', 'most frequently asked',
        'latest questions asked by', 'last 30 days questions',
    ]
    has_marker = any(m in q for m in explicit_markers)

    question_markers = [
        'question', 'questions', 'problem', 'problems', 'coding',
        'interview', 'practice', 'prepare', 'preparation', 'top',
        'frequent', 'common', 'trending', 'latest', 'recent'
    ]
    has_question_signal = any(m in q for m in question_markers)

    company = _resolve_leetcode_company(tracker, q, companies)
    return bool(company and (has_marker or has_question_signal))


def _extract_leetcode_query_filters(text: str) -> Dict[str, Any]:
    q = (text or '').lower()
    filters: Dict[str, Any] = {
        'difficulty': None,
        'top_n': None,
        'sort_by_frequency': False,
        'analytics': False,
        'preparation': False,
    }

    if 'easy' in q:
        filters['difficulty'] = 'easy'
    elif 'medium' in q:
        filters['difficulty'] = 'medium'
    elif 'hard' in q:
        filters['difficulty'] = 'hard'

    top_match = re.search(r'\btop\s+(\d{1,2})\b', q)
    if top_match:
        try:
            filters['top_n'] = max(1, min(50, int(top_match.group(1))))
        except Exception:
            filters['top_n'] = None

    if re.search(r'\blatest\s+question\b', q) and not re.search(r'\blatest\s+questions\b', q):
        filters['top_n'] = 1

    if any(k in q for k in ['frequent', 'frequently', 'most common', 'common', 'trending', 'top interview questions']):
        filters['sort_by_frequency'] = True

    if any(k in q for k in ['how many', 'difficulty distribution', 'percentage', 'percent', 'distribution', 'mostly']):
        filters['analytics'] = True

    if any(k in q for k in ['practice', 'prepare', 'preparation', 'crack', 'recommend']):
        filters['preparation'] = True
        filters['sort_by_frequency'] = True
        if filters['top_n'] is None:
            filters['top_n'] = 30

    return filters


def _build_leetcode_pdf_report(
    company: str,
    time_label: str,
    source_csv_path: str,
    questions_df: pd.DataFrame,
    output_pdf_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    df = questions_df.copy()
    for col in ['Title', 'Difficulty', 'URL', 'Frequency %']:
        if col not in df.columns:
            df[col] = ''

    def _to_percent_number(v: Any) -> float:
        cleaned = str(v).replace('%', '').strip()
        try:
            return float(cleaned)
        except Exception:
            return 0.0

    df['FrequencyNumeric'] = df['Frequency %'].apply(_to_percent_number)
    df = df.sort_values(['FrequencyNumeric', 'Title'], ascending=[False, True]).reset_index(drop=True)

    easy_count = int((df['Difficulty'].astype(str).str.lower() == 'easy').sum())
    medium_count = int((df['Difficulty'].astype(str).str.lower() == 'medium').sum())
    hard_count = int((df['Difficulty'].astype(str).str.lower() == 'hard').sum())

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    story: List[Any] = []

    story.append(Paragraph("EduPlus Placement Analytics", styles['Title']))
    story.append(Paragraph("LeetCode Companywise Interview Questions Report", styles['Heading2']))
    story.append(Spacer(1, 8))

    generated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
    summary_text = (
        f"Company: <b>{company.title()}</b><br/>"
        f"Time Window: <b>{time_label}</b><br/>"
        f"Source File: <b>{os.path.basename(source_csv_path)}</b><br/>"
        f"Generated At (UTC): <b>{generated_at}</b><br/>"
        f"Total Questions: <b>{len(df)}</b><br/>"
        f"Difficulty Split - Easy: <b>{easy_count}</b>, Medium: <b>{medium_count}</b>, Hard: <b>{hard_count}</b>"
    )
    story.append(Paragraph(summary_text, styles['BodyText']))
    story.append(Spacer(1, 12))

    table_data: List[List[str]] = [["S.No", "Title", "Difficulty", "Frequency", "URL"]]
    for i, row in df.iterrows():
        table_data.append([
            str(i + 1),
            str(row.get('Title', '')),
            str(row.get('Difficulty', '')),
            str(row.get('Frequency %', '')),
            str(row.get('URL', '')),
        ])

    questions_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[0.45 * inch, 2.35 * inch, 0.95 * inch, 0.9 * inch, 2.55 * inch],
    )
    questions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))

    story.append(questions_table)
    doc.build(story)


class ActionGetLeetCodeCompanyQuestions(Action):
    def name(self) -> Text:
        return "action_get_leetcode_company_questions"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        companies = _list_leetcode_companies()
        if not companies:
            dispatcher.utter_message(
                text="LeetCode companywise dataset is not available right now. Please try again later."
            )
            return []

        raw_text = tracker.latest_message.get('text', '') or ''
        company = _resolve_leetcode_company(tracker, raw_text, companies)
        if not company:
            dispatcher.utter_message(
                text="Please mention a company name for the LeetCode interview questions report, for example Amazon, Google, or Microsoft."
            )
            return []

        csv_file_name, time_label = _resolve_leetcode_time_file(raw_text)
        csv_path = os.path.join(LEETCODE_DATA_DIR, company, csv_file_name)

        if not os.path.exists(csv_path):
            fallback_path = os.path.join(LEETCODE_DATA_DIR, company, 'all.csv')
            if os.path.exists(fallback_path):
                csv_path = fallback_path
                csv_file_name = 'all.csv'
                time_label = 'All Time'
            else:
                dispatcher.utter_message(
                    text=f"I could not find question data for {company.title()} right now."
                )
                return []

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            dispatcher.utter_message(text=f"I could not read the dataset file due to: {e}")
            return []

        if df.empty:
            dispatcher.utter_message(
                text=f"No questions were found for {company.title()} in the selected time window ({time_label})."
            )
            return []

        filters = _extract_leetcode_query_filters(raw_text)
        filtered_df = df.copy()

        for col in ['Title', 'Difficulty', 'URL', 'Frequency %']:
            if col not in filtered_df.columns:
                filtered_df[col] = ''

        def _freq_num(v: Any) -> float:
            cleaned = str(v).replace('%', '').strip()
            try:
                return float(cleaned)
            except Exception:
                return 0.0

        filtered_df['FrequencyNumeric'] = filtered_df['Frequency %'].apply(_freq_num)

        if filters['difficulty']:
            filtered_df = filtered_df[
                filtered_df['Difficulty'].astype(str).str.lower() == filters['difficulty']
            ]

        if filters['sort_by_frequency']:
            filtered_df = filtered_df.sort_values(['FrequencyNumeric', 'Title'], ascending=[False, True])

        if filters['top_n'] is not None:
            filtered_df = filtered_df.head(int(filters['top_n']))

        filtered_df = filtered_df.reset_index(drop=True)

        if filtered_df.empty:
            detail = f" for difficulty '{filters['difficulty']}'" if filters['difficulty'] else ''
            dispatcher.utter_message(
                text=(
                    f"No questions were found for {company.title()} in {time_label}{detail}. "
                    "Try another time range or remove difficulty filters."
                )
            )
            return []

        os.makedirs(LEETCODE_REPORTS_DIR, exist_ok=True)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        report_name = (
            f"leetcode_{_safe_slug(company)}_{_safe_slug(csv_file_name.replace('.csv', ''))}_{timestamp}_{uuid.uuid4().hex[:8]}.pdf"
        )
        report_path = os.path.join(LEETCODE_REPORTS_DIR, report_name)

        try:
            _build_leetcode_pdf_report(
                company=company,
                time_label=time_label,
                source_csv_path=csv_path,
                questions_df=filtered_df,
                output_pdf_path=report_path,
            )
        except Exception as e:
            dispatcher.utter_message(text=f"I could not generate the PDF report due to: {e}")
            return []

        easy_count = int((filtered_df.get('Difficulty', pd.Series(dtype=str)).astype(str).str.lower() == 'easy').sum())
        medium_count = int((filtered_df.get('Difficulty', pd.Series(dtype=str)).astype(str).str.lower() == 'medium').sum())
        hard_count = int((filtered_df.get('Difficulty', pd.Series(dtype=str)).astype(str).str.lower() == 'hard').sum())
        download_url = f"{LEETCODE_REPORT_BASE_URL.rstrip('/')}/api/reports/{report_name}"

        stats_lines: List[str] = []
        if filters['analytics']:
            total = max(1, len(filtered_df))
            easy_pct = (easy_count / total) * 100.0
            med_pct = (medium_count / total) * 100.0
            hard_pct = (hard_count / total) * 100.0
            dominant = max(
                [('Easy', easy_count), ('Medium', medium_count), ('Hard', hard_count)],
                key=lambda x: x[1]
            )[0]
            stats_lines.append(
                f"Difficulty Distribution: Easy {easy_count} ({easy_pct:.1f}%), "
                f"Medium {medium_count} ({med_pct:.1f}%), Hard {hard_count} ({hard_pct:.1f}%)"
            )
            stats_lines.append(f"Majority difficulty in this set: {dominant}")

        filter_line = []
        if filters['difficulty']:
            filter_line.append(f"Difficulty filter: {filters['difficulty'].title()}")
        if filters['top_n'] is not None:
            filter_line.append(f"Top N applied: {filters['top_n']}")
        if filters['sort_by_frequency']:
            filter_line.append("Sorted by frequency")

        extra = "\n" + "\n".join(stats_lines) if stats_lines else ""
        if filter_line:
            extra += "\n" + " | ".join(filter_line)

        dispatcher.utter_message(
            text=(
                f"Below is your report for {company.title()} ({time_label}).\n"
                f"Questions: {len(filtered_df)} | Easy: {easy_count} | Medium: {medium_count} | Hard: {hard_count}"
                f"{extra}\n"
                f"Downloadable PDF: {download_url}"
            )
        )
        return []


class ActionHandleTemplateQueries(Action):
    def name(self) -> Text:
        return "action_handle_template_queries"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        text = (tracker.latest_message.get('text', '') or '').lower()
        text_normalized = re.sub(r'\s+', ' ', text).strip()

        # Compatibility path: handle LeetCode report queries through this existing action
        # so older models that don't know the new action name still work.
        companies = _list_leetcode_companies()
        if _is_leetcode_company_questions_query(tracker, text, companies):
            return ActionGetLeetCodeCompanyQuestions().run(dispatcher, tracker, domain)

        df = DataStore.get_df().copy()

        if df.empty:
            dispatcher.utter_message(text="Placement dataset is currently unavailable.")
            return []

        for col in ['avg_package_lpa', 'max_package_lpa', 'min_cgpa', 'hiring_intensity']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df['round_count'] = df.apply(_round_count_from_row, axis=1)

        # 10) Hiring Intensity templates
        if 'hiring the most' in text or 'hire the most students' in text:
            top = df.sort_values('hiring_intensity', ascending=False)[['company_name', 'hiring_intensity']].head(3).values.tolist()
            response = (
                "You asked which companies are hiring the most students.\n\n"
                "Based on the placement dataset, the companies with the highest hiring intensity include:\n\n"
                + "\n".join([f"• {r[0]} – Hiring intensity: {r[1]:.1f}" for r in top])
                + "\n\nThese companies usually recruit a larger number of candidates during the placement season, which can increase the chances of selection.\n\n"
                "If you'd like, I can also show you their package ranges and eligibility criteria."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'highest hiring intensity' in text:
            row = df.sort_values('hiring_intensity', ascending=False).iloc[0]
            response = (
                "You asked which company has the highest hiring intensity.\n\n"
                f"According to the placement dataset, {row['company_name']} currently has the highest hiring intensity with a value of {row['hiring_intensity']:.1f}.\n\n"
                "This means the company typically recruits a larger batch of students compared to others during placements.\n\n"
                "If you'd like, I can also show you companies with the next highest hiring levels."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'hire the least' in text or 'least students' in text or 'fewest students' in text:
            low = df.sort_values('hiring_intensity', ascending=True)[['company_name', 'hiring_intensity']].head(2).values.tolist()
            response = (
                "You asked which companies hire the fewest students.\n\n"
                "From the placement dataset, the companies with relatively lower hiring intensity include:\n\n"
                + "\n".join([f"• {r[0]} – Hiring intensity: {r[1]:.1f}" for r in low])
                + "\n\nThese companies usually have more competitive selection processes and fewer openings.\n\n"
                "If you'd like, I can also show you companies that hire larger batches of students."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'high hiring chances' in text or 'high hiring chance' in text:
            top = df.sort_values('hiring_intensity', ascending=False)['company_name'].head(3).tolist()
            response = (
                "You asked which companies offer higher chances of selection.\n\n"
                "Based on the dataset, companies with higher hiring intensity generally include:\n\n"
                + "\n".join([f"• {c}" for c in top])
                + "\n\nThese companies tend to recruit more students in each placement cycle, which may improve the chances of getting selected.\n\n"
                "If you'd like, I can also show you which of these companies offer the best packages."
            )
            dispatcher.utter_message(text=response)
            return []

        # 11) Comparison templates and 17) decision making templates
        if any(k in text for k in ['compare', 'which is better', 'should i focus on', 'higher average package', 'easier eligibility']):
            names = _resolve_two_companies(df, tracker, text)
            if len(names) < 2:
                dispatcher.utter_message(text="Please mention two company names so I can compare them.")
                return []
            r1 = df[df['company_name'] == names[0]].iloc[0]
            r2 = df[df['company_name'] == names[1]].iloc[0]

            if 'higher average package' in text:
                winner = r1['company_name'] if r1['avg_package_lpa'] >= r2['avg_package_lpa'] else r2['company_name']
                response = (
                    f"You asked which company offers a higher average package between {r1['company_name']} and {r2['company_name']}.\n\n"
                    "According to the placement dataset:\n\n"
                    f"• {r1['company_name']} – Average package: {r1['avg_package_lpa']:.2f} LPA\n"
                    f"• {r2['company_name']} – Average package: {r2['avg_package_lpa']:.2f} LPA\n\n"
                    f"Based on this data, {winner} offers the higher average package.\n\n"
                    "If you'd like, I can also compare their maximum packages or interview processes."
                )
            elif 'easier eligibility' in text:
                easy = r1['company_name'] if (r1['min_cgpa'] < r2['min_cgpa'] or _backlogs_allowed_count(r1['backlogs_allowed']) > _backlogs_allowed_count(r2['backlogs_allowed'])) else r2['company_name']
                response = (
                    f"You asked which company has easier eligibility between {r1['company_name']} and {r2['company_name']}.\n\n"
                    "Here’s a comparison based on the dataset:\n\n"
                    f"{r1['company_name']}\n"
                    f"• Minimum CGPA: {r1['min_cgpa']}\n"
                    f"• Backlogs allowed: {_backlogs_allowed_count(r1['backlogs_allowed'])}\n"
                    f"• Allowed departments: {r1['allowed_departments']}\n\n"
                    f"{r2['company_name']}\n"
                    f"• Minimum CGPA: {r2['min_cgpa']}\n"
                    f"• Backlogs allowed: {_backlogs_allowed_count(r2['backlogs_allowed'])}\n"
                    f"• Allowed departments: {r2['allowed_departments']}\n\n"
                    f"Based on these criteria, {easy} may have slightly easier eligibility requirements.\n\n"
                    "If you'd like, I can also compare their interview difficulty or salary packages."
                )
            elif 'compare' in text and 'package' in text:
                winner = r1['company_name'] if r1['avg_package_lpa'] >= r2['avg_package_lpa'] else r2['company_name']
                response = (
                    f"You asked for a package comparison between {r1['company_name']} and {r2['company_name']}.\n\n"
                    "Here is a quick overview:\n\n"
                    f"{r1['company_name']}\n"
                    f"• Average Package: {r1['avg_package_lpa']:.2f} LPA\n"
                    f"• Maximum Package: {r1['max_package_lpa']:.2f} LPA\n\n"
                    f"{r2['company_name']}\n"
                    f"• Average Package: {r2['avg_package_lpa']:.2f} LPA\n"
                    f"• Maximum Package: {r2['max_package_lpa']:.2f} LPA\n\n"
                    f"Based on this comparison, {winner} offers a slightly higher package, but both companies provide strong career opportunities.\n\n"
                    "If you'd like, I can also compare their eligibility criteria or interview processes."
                )
            elif 'should i focus on' in text or 'which is better' in text:
                sal_w = r1['company_name'] if r1['avg_package_lpa'] >= r2['avg_package_lpa'] else r2['company_name']
                chance_w = r1['company_name'] if r1['hiring_intensity'] >= r2['hiring_intensity'] else r2['company_name']
                response = (
                    f"You asked which is better between {r1['company_name']} and {r2['company_name']}.\n\n"
                    "Here’s a quick comparison based on the dataset:\n\n"
                    f"{r1['company_name']}\n"
                    f"• Average package: {r1['avg_package_lpa']:.2f} LPA\n"
                    f"• Hiring intensity: {r1['hiring_intensity']:.1f}\n"
                    f"• Interview rounds: {int(r1['round_count'])}\n\n"
                    f"{r2['company_name']}\n"
                    f"• Average package: {r2['avg_package_lpa']:.2f} LPA\n"
                    f"• Hiring intensity: {r2['hiring_intensity']:.1f}\n"
                    f"• Interview rounds: {int(r2['round_count'])}\n\n"
                    f"In general:\n• If you are looking for higher salary, {sal_w} may be better.\n• If you are looking for higher chances of selection, {chance_w} might be a better option.\n\n"
                    "If you'd like, I can also compare their eligibility criteria or preparation difficulty."
                )
            else:
                response = "Please ask comparison as package, better company, higher average package, or easier eligibility."

            dispatcher.utter_message(text=response)
            return []

        if 'more interview rounds' in text:
            ranked = df.sort_values('round_count', ascending=False)[['company_name', 'round_count']].head(2).values.tolist()
            winner = ranked[0][0]
            response = (
                "You asked which company has more interview rounds.\n\n"
                "According to the dataset:\n\n"
                f"• {ranked[0][0]} – {int(ranked[0][1])} interview rounds\n"
                f"• {ranked[1][0]} – {int(ranked[1][1])} interview rounds\n\n"
                f"This means {winner} has a longer interview process.\n\n"
                "If you'd like, I can also explain what happens in each round."
            )
            dispatcher.utter_message(text=response)
            return []

        # 12) Recommendations
        if 'should i target' in text or 'companies to target' in text:
            a = df.sort_values('max_package_lpa', ascending=False).iloc[0]
            b = df.sort_values('hiring_intensity', ascending=False).iloc[0]
            c = df.assign(score=(10 - abs(df['min_cgpa'] - 7.5)) + df['avg_package_lpa'] / 5.0).sort_values('score', ascending=False).iloc[0]
            response = (
                "You asked which companies you should target for placements.\n\n"
                "Based on the placement dataset, some of the companies worth targeting include:\n\n"
                f"• {a['company_name']} – Strong package and good roles\n"
                f"• {b['company_name']} – High hiring intensity\n"
                f"• {c['company_name']} – Balanced eligibility and salary\n\n"
                "Your ideal target companies usually depend on factors like your CGPA, skills, and preparation level.\n\n"
                "If you'd like, I can also recommend companies based on your CGPA or skillset."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'best for high salary' in text:
            top = df.sort_values('max_package_lpa', ascending=False)[['company_name', 'max_package_lpa']].head(3).values.tolist()
            response = (
                "You asked which companies offer the highest salary packages.\n\n"
                "According to the placement dataset, the top companies for high salary include:\n\n"
                + "\n".join([f"• {r[0]} – Maximum package: {r[1]:.2f} LPA" for r in top])
                + "\n\nThese companies usually belong to higher placement tiers and have competitive interview processes.\n\n"
                "If you'd like, I can also show you the preparation topics required for these companies."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'easier selection' in text or 'easiest to get into' in text or 'easier to crack' in text or 'best chance of selection' in text:
            cand = df.copy()
            cand['ease_score'] = (10 - cand['min_cgpa']) + cand['hiring_intensity'] - cand['round_count']
            top = cand.sort_values('ease_score', ascending=False)['company_name'].head(2).tolist()
            response = (
                "You asked which companies have easier selection processes.\n\n"
                "Based on the dataset, companies with relatively easier selection usually have:\n\n"
                "• Lower CGPA requirements\n"
                "• Higher hiring intensity\n"
                "• Fewer interview rounds\n\n"
                "Examples include:\n\n"
                + "\n".join([f"• {c}" for c in top])
                + "\n\nThese companies can be a good starting point for placement preparation.\n\n"
                "If you'd like, I can also suggest companies that match your eligibility criteria."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'fewer interview rounds' in text or 'shorter interview' in text:
            few = df.sort_values('round_count', ascending=True)[['company_name', 'round_count']].head(2).values.tolist()
            response = (
                "You asked which companies have shorter interview processes.\n\n"
                "From the placement dataset, the companies with fewer interview rounds include:\n\n"
                + "\n".join([f"• {r[0]} – {int(r[1])} rounds" for r in few])
                + "\n\nThese companies typically complete their hiring process faster compared to companies with multiple technical rounds.\n\n"
                "If you'd like, I can also show you companies with the highest salary packages."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'high hiring intensity' in text and 'companies have' in text:
            top = df.sort_values('hiring_intensity', ascending=False)['company_name'].head(3).tolist()
            response = (
                "You asked which companies have high hiring intensity.\n\n"
                "Based on the placement dataset, the companies that recruit the largest number of students include:\n\n"
                + "\n".join([f"• {c}" for c in top])
                + "\n\nThese companies usually provide more placement opportunities due to their larger hiring volume.\n\n"
                "If you'd like, I can also show you their salary packages or eligibility criteria."
            )
            dispatcher.utter_message(text=response)
            return []

        # 13) Strategy templates
        if any(k in text for k in ['how should i prepare for', 'what should i study for', 'most important for', 'preparation is required for']):
            company, _ = resolve_company(tracker)
            if not company:
                dispatcher.utter_message(text="Please mention the company name for strategy guidance.")
                return []
            row = df[df['company_name'] == company].iloc[0]
            rounds = int(row['round_count'])
            key_skill = _split_items(str(row.get('required_skills', 'Programming')))[0] if _split_items(str(row.get('required_skills', ''))) else 'programming'
            response = (
                f"You asked how you should prepare for {company} placements.\n\n"
                "Based on the placement dataset, a good preparation strategy would include:\n\n"
                "• Practicing Data Structures and Algorithms problems\n"
                f"• Strengthening your knowledge of {key_skill}\n"
                "• Reviewing concepts in OOPS and DBMS\n"
                "• Practicing coding problems and technical interview questions\n\n"
                f"Since {company} usually has {rounds} interview rounds, it’s helpful to focus on both coding ability and technical fundamentals.\n\n"
                "If you'd like, I can also suggest the most important topics to prepare for this company."
            )
            dispatcher.utter_message(text=response)
            return []

        # 14) Eligibility + Strategy combined
        if 'can i apply for' in text and 'cgpa' in text:
            company, _ = resolve_company(tracker)
            if not company:
                dispatcher.utter_message(text="Please mention the company name for eligibility check.")
                return []
            row = df[df['company_name'] == company].iloc[0]
            cgpa = _extract_number(text, 0)
            bl_match = re.search(r'(\d+)\s*backlog', text)
            backlogs = int(bl_match.group(1)) if bl_match else 0
            req_cgpa = float(row['min_cgpa'])
            max_bl = _backlogs_allowed_count(row['backlogs_allowed'])
            ok = cgpa >= req_cgpa and backlogs <= max_bl
            result_line = (
                "If your CGPA and backlog count meet these requirements, you are eligible to apply for this company."
                if ok else
                "If not, you may want to consider companies with more flexible eligibility criteria."
            )
            response = (
                f"You asked whether you can apply for {company} with a CGPA of {cgpa:.2f} and {backlogs} backlog(s).\n\n"
                "Here are the eligibility requirements for this company:\n\n"
                f"• Minimum CGPA required: {req_cgpa}\n"
                f"• Maximum backlogs allowed: {max_bl}\n\n"
                f"{result_line}\n\n"
                "If you'd like, I can also show you companies that match your current eligibility."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'which companies can i apply to with' in text and 'cgpa' in text:
            cgpa = _extract_number(text, 7.0)
            filt = df[df['min_cgpa'] <= cgpa].sort_values('min_cgpa')[['company_name', 'min_cgpa']].head(3).values.tolist()
            response = (
                f"You asked which companies you can apply to with a CGPA of {cgpa:.2f}.\n\n"
                "Based on the placement dataset, the companies where your CGPA meets the eligibility criteria include:\n\n"
                + "\n".join([f"• {r[0]} – Minimum CGPA: {r[1]}" for r in filt])
                + "\n\nThese companies may be suitable options based on your current CGPA.\n\n"
                "If you'd like, I can also help you identify companies with higher hiring chances."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'best for students with low cgpa' in text:
            low = df.sort_values('min_cgpa')[['company_name', 'min_cgpa']].head(2).values.tolist()
            response = (
                "You asked which companies are suitable for students with lower CGPA requirements.\n\n"
                "Based on the dataset, the companies with relatively flexible CGPA criteria include:\n\n"
                + "\n".join([f"• {r[0]} – Minimum CGPA: {r[1]}" for r in low])
                + "\n\nThese companies often focus more on technical skills and interview performance rather than only academic scores.\n\n"
                "If you'd like, I can also suggest how to prepare for these companies."
            )
            dispatcher.utter_message(text=response)
            return []

        # 15) Salary + hiring probability
        if 'high salary and high hiring' in text:
            cand = df.copy()
            cand['score'] = cand['avg_package_lpa'] + cand['hiring_intensity']
            top = cand.sort_values('score', ascending=False)[['company_name', 'avg_package_lpa', 'hiring_intensity']].head(2).values.tolist()
            response = (
                "You asked which companies offer both high salary packages and high hiring intensity.\n\n"
                "Based on the placement dataset, the companies that balance both factors include:\n\n"
                + "\n".join([f"• {r[0]} – Average package: {r[1]:.2f} LPA | Hiring intensity: {r[2]:.1f}" for r in top])
                + "\n\nThese companies provide good salary opportunities while also hiring a relatively larger number of students.\n\n"
                "If you'd like, I can also show you companies offering the absolute highest packages."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'good packages but hire many' in text:
            filt = df[df['hiring_intensity'] >= df['hiring_intensity'].median()].sort_values('avg_package_lpa', ascending=False)[['company_name', 'avg_package_lpa']].head(2).values.tolist()
            response = (
                "You asked which companies offer good salary packages while also hiring a larger number of students.\n\n"
                "According to the placement dataset, examples include:\n\n"
                + "\n".join([f"• {r[0]} – Average package: {r[1]:.2f} LPA" for r in filt])
                + "\n\nThese companies provide a balance between strong salary packages and higher placement opportunities.\n\n"
                "If you'd like, I can also show you companies with the highest hiring intensity overall."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'high salary but low hiring' in text:
            filt = df[df['hiring_intensity'] <= df['hiring_intensity'].quantile(0.35)].sort_values('max_package_lpa', ascending=False)[['company_name', 'max_package_lpa', 'hiring_intensity']].head(2).values.tolist()
            response = (
                "You asked which companies offer high salary packages but hire fewer students.\n\n"
                "Based on the dataset, companies in this category include:\n\n"
                + "\n".join([f"• {r[0]} – Maximum package: {r[1]:.2f} LPA | Hiring intensity: {r[2]:.1f}" for r in filt])
                + "\n\nThese companies typically have very competitive selection processes with limited openings.\n\n"
                "If you'd like, I can also show you companies with higher chances of selection."
            )
            dispatcher.utter_message(text=response)
            return []

        # 16/18) Advanced and complex analytics
        if 'tier 1' in text and ('offer more than' in text or 'above' in text) and 'lpa' in text and 'cgpa' not in text:
            x = _extract_number(text, 20)
            filt = df[df['company_tier'].astype(str).str.contains('tier-1', case=False, na=False) & (df['avg_package_lpa'] > x)][['company_name', 'avg_package_lpa']].head(5).values.tolist()
            response = (
                f"You asked which Tier 1 companies offer packages higher than {x:.1f} LPA.\n\n"
                "Based on the placement dataset, the companies that meet both criteria include:\n\n"
                + "\n".join([f"• {r[0]} – Tier: 1 | Average package: {r[1]:.2f} LPA" for r in filt])
                + "\n\nThese companies belong to the top placement tier and offer competitive salary packages.\n\n"
                "If you'd like, I can also show you their interview processes or eligibility requirements."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'require dsa' in text and ('system design' in text or 'and' in text):
            filt = df[df['required_skills'].astype(str).str.lower().str.contains('dsa', na=False) & df['required_skills'].astype(str).str.lower().str.contains('system', na=False)]
            names = filt['company_name'].head(5).tolist()
            response = (
                "You asked which companies require both DSA and System Design.\n\n"
                "According to the placement dataset, the companies that commonly expect these skills include:\n\n"
                + "\n".join([f"• {c}" for c in names])
                + "\n\nThese companies usually test these skills through coding rounds, technical interviews, or system design discussions.\n\n"
                "If you'd like, I can also suggest preparation topics for these companies."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'more than' in text and 'interview rounds' in text:
            x = int(_extract_number(text, 3))
            filt = df[df['round_count'] > x][['company_name', 'round_count']].sort_values('round_count', ascending=False).head(5).values.tolist()
            response = (
                f"You asked which companies have more than {x} interview rounds.\n\n"
                "Based on the placement dataset, the companies with longer interview processes include:\n\n"
                + "\n".join([f"• {r[0]} – {int(r[1])} rounds" for r in filt])
                + "\n\nThese companies usually conduct multiple technical interviews before the final HR round.\n\n"
                "If you'd like, I can also show you companies with shorter hiring processes."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'allow backlogs' in text and 'high salary' in text:
            filt = df[df['backlogs_allowed'].apply(_backlogs_allowed_count) > 0].sort_values('max_package_lpa', ascending=False)[['company_name', 'max_package_lpa', 'backlogs_allowed']].head(5).values.tolist()
            response = (
                "You asked which companies allow backlogs while still offering strong salary packages.\n\n"
                "From the dataset, the companies that meet these conditions include:\n\n"
                + "\n".join([f"• {r[0]} – Max package: {r[1]:.2f} LPA | Backlogs allowed: {int(r[2])}" for r in filt])
                + "\n\nThese companies provide good opportunities for students who meet technical requirements despite having backlogs.\n\n"
                "If you'd like, I can also show you their eligibility criteria or hiring intensity."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'require cgpa above' in text and 'offer more than' in text and 'lpa' in text:
            nums = re.findall(r'(\d+(?:\.\d+)?)', text)
            x = float(nums[0]) if len(nums) >= 1 else 8.0
            y = float(nums[1]) if len(nums) >= 2 else 20.0
            filt = df[(df['min_cgpa'] > x) & (df['avg_package_lpa'] > y)][['company_name', 'min_cgpa', 'avg_package_lpa']].head(5).values.tolist()
            response = (
                f"You asked which companies require CGPA above {x:.1f} and offer packages higher than {y:.1f} LPA.\n\n"
                "According to the placement dataset, the companies that match these criteria include:\n\n"
                + "\n".join([f"• {r[0]} – Minimum CGPA: {r[1]} | Average package: {r[2]:.2f} LPA" for r in filt])
                + "\n\nThese companies typically have higher eligibility requirements and competitive interview processes.\n\n"
                "If you'd like, I can also show you their interview rounds or preparation topics."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'hire the most students' in text and 'good packages' in text:
            cand = df.copy()
            cand['score'] = cand['hiring_intensity'] + cand['avg_package_lpa']
            top = cand.sort_values('score', ascending=False)[['company_name', 'avg_package_lpa', 'hiring_intensity']].head(2).values.tolist()
            response = (
                "You asked which companies hire a large number of students while also offering good salary packages.\n\n"
                "From the placement dataset, examples include:\n\n"
                + "\n".join([f"• {r[0]} – Average package: {r[1]:.2f} LPA | Hiring intensity: {r[2]:.1f}" for r in top])
                + "\n\nThese companies provide a balance between strong salary packages and higher placement opportunities.\n\n"
                "If you'd like, I can also show you companies offering the highest packages overall."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'best salary vs difficulty ratio' in text:
            cand = df.copy()
            cand['ratio'] = cand['avg_package_lpa'] / (cand['difficulty_factor'].replace(0, 1))
            top = cand.sort_values('ratio', ascending=False)[['company_name', 'avg_package_lpa', 'hiring_intensity']].head(2).values.tolist()
            response = (
                "You asked which company provides the best balance between salary and difficulty of selection.\n\n"
                "From the placement dataset, companies that balance good salary packages with moderate hiring difficulty include:\n\n"
                + "\n".join([f"• {r[0]} – Average package: {r[1]:.2f} LPA | Hiring intensity: {r[2]:.1f}" for r in top])
                + "\n\nThese companies often provide strong salary opportunities without extremely strict eligibility requirements.\n\n"
                "If you'd like, I can also show you the highest paying companies overall."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'tier 1' in text and 'cgpa above' in text and 'lpa' in text:
            nums = re.findall(r'(\d+(?:\.\d+)?)', text)
            x = float(nums[0]) if len(nums) >= 1 else 20.0
            y = float(nums[1]) if len(nums) >= 2 else 8.0
            filt = df[df['company_tier'].astype(str).str.contains('tier-1', case=False, na=False) & (df['avg_package_lpa'] > x) & (df['min_cgpa'] > y)][['company_name', 'avg_package_lpa', 'min_cgpa']].head(5).values.tolist()
            response = (
                f"You asked which Tier 1 companies offer packages above {x:.1f} LPA and require CGPA higher than {y:.1f}.\n\n"
                "From the placement dataset, the companies matching these conditions include:\n\n"
                + "\n".join([f"• {r[0]} – Tier 1 | Avg package: {r[1]:.2f} LPA | CGPA: {r[2]}" for r in filt])
                + "\n\nThese companies generally have competitive hiring processes and strong salary packages.\n\n"
                "If you'd like, I can also show you their interview rounds or preparation topics."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'high hiring intensity' in text and ('fewer interview rounds' in text or 'short interview' in text):
            cand = df[df['hiring_intensity'] >= df['hiring_intensity'].median()].sort_values(['round_count', 'hiring_intensity'], ascending=[True, False])
            data = cand[['company_name', 'hiring_intensity', 'round_count']].head(2).values.tolist()
            response = (
                "You asked which companies have high hiring intensity but relatively shorter interview processes.\n\n"
                "According to the dataset, examples include:\n\n"
                + "\n".join([f"• {r[0]} – Hiring intensity: {r[1]:.1f} | Interview rounds: {int(r[2])}" for r in data])
                + "\n\nThese companies may offer higher chances of selection with a faster hiring process.\n\n"
                "If you'd like, I can also show you their salary packages."
            )
            dispatcher.utter_message(text=response)
            return []

        # 19) Filtering questions
        if text.startswith('show companies with') or ('companies with' in text and ('below' in text or 'above' in text or 'allow backlogs' in text)):
            criteria = text.replace('show companies with', '').strip()
            filt = df
            label = 'value'

            if 'cgpa' in text and 'below' in text:
                v = _extract_number(text, 7.5)
                filt = df[df['min_cgpa'] < v]
                label = 'Minimum CGPA'
            elif ('max package' in text or 'package' in text) and ('above' in text or 'more than' in text):
                v = _extract_number(text, 25)
                filt = df[df['max_package_lpa'] > v]
                label = 'Maximum package'
            elif 'hiring intensity' in text and ('above' in text or 'more than' in text):
                v = _extract_number(text, 10)
                filt = df[df['hiring_intensity'] > v]
                label = 'Hiring intensity'
            elif 'allow backlogs' in text:
                filt = df[df['backlogs_allowed'].apply(_backlogs_allowed_count) > 0]
                label = 'Backlogs allowed'

            rows = filt.head(5)
            vals = []
            for _, r in rows.iterrows():
                if label == 'Minimum CGPA':
                    vals.append((r['company_name'], r['min_cgpa']))
                elif label == 'Maximum package':
                    vals.append((r['company_name'], f"{r['max_package_lpa']:.2f} LPA"))
                elif label == 'Hiring intensity':
                    vals.append((r['company_name'], f"{r['hiring_intensity']:.1f}"))
                else:
                    vals.append((r['company_name'], int(_backlogs_allowed_count(r['backlogs_allowed']))))

            response = (
                f"You asked to see companies where {criteria}.\n\n"
                "Based on the placement dataset, the companies that match this condition include:\n\n"
                + "\n".join([f"• {v[0]} – {label}: {v[1]}" for v in vals])
                + "\n\nThese companies meet the specified requirement and may be suitable options depending on your eligibility.\n\n"
                "If you'd like, I can also help you compare these companies based on salary or hiring chances."
            )
            dispatcher.utter_message(text=response)
            return []

        # 20) Ranking + Top N templates
        if text.startswith('rank companies by'):
            metric = text.replace('rank companies by', '').strip()
            if 'average package' in metric:
                ranked = df.sort_values('avg_package_lpa', ascending=False)[['company_name', 'avg_package_lpa']].head(5).values.tolist()
                explanation = 'average package'
            elif 'hiring intensity' in metric:
                ranked = df.sort_values('hiring_intensity', ascending=False)[['company_name', 'hiring_intensity']].head(5).values.tolist()
                explanation = 'hiring intensity'
            elif 'cgpa requirement' in metric or 'cgpa' in metric:
                ranked = df.sort_values('min_cgpa', ascending=False)[['company_name', 'min_cgpa']].head(5).values.tolist()
                explanation = 'CGPA requirement'
            else:
                ranked = df.sort_values('avg_package_lpa', ascending=False)[['company_name', 'avg_package_lpa']].head(5).values.tolist()
                explanation = 'average package'

            lines = []
            for i, r in enumerate(ranked, start=1):
                val = f"{r[1]:.2f}" if isinstance(r[1], float) else str(r[1])
                lines.append(f"{i}. {r[0]} – {val}")

            response = (
                f"You asked to rank companies based on {metric}.\n\n"
                "Here is the ranking according to the placement dataset:\n\n"
                + "\n".join(lines)
                + f"\n\nThis ranking helps compare companies based on {explanation}.\n\n"
                "If you'd like, I can also show you rankings based on salary, hiring intensity, or eligibility criteria."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'top' in text and 'highest paying companies' in text:
            n = _extract_top_n(text, 5)
            ranked = df.sort_values('max_package_lpa', ascending=False)[['company_name', 'max_package_lpa']].head(n).values.tolist()
            lines = [f"{i}. {r[0]} – Maximum package: {r[1]:.2f} LPA" for i, r in enumerate(ranked, start=1)]
            response = (
                f"You asked for the top {n} highest paying companies.\n\n"
                "Based on the placement dataset, the companies offering the highest salary packages include:\n\n"
                + "\n".join(lines)
                + "\n\nThese companies usually belong to higher placement tiers and have competitive interview processes.\n\n"
                "If you'd like, I can also show you companies with higher hiring chances."
            )
            dispatcher.utter_message(text=response)
            return []

        if 'most preparation topics' in text:
            prep_cols = ['prep_dsa_topics', 'prep_system_design_topics', 'prep_oops_topics', 'prep_dbms_topics', 'prep_hr_topics']

            def _topic_count(row):
                count = 0
                for c in prep_cols:
                    v = str(row.get(c, '')).strip()
                    if v and v.upper() != 'NA':
                        count += len(_split_items(v)) if _split_items(v) else 1
                return count

            tmp = df.copy()
            tmp['prep_topic_count'] = tmp.apply(_topic_count, axis=1)
            top = tmp.sort_values('prep_topic_count', ascending=False)[['company_name', 'prep_topic_count']].head(5).values.tolist()

            response = (
                "You asked which companies require the most preparation topics.\n\n"
                "Based on the placement dataset, the companies with the broadest preparation coverage include:\n\n"
                + "\n".join([f"• {r[0]} – Preparation topics tracked: {int(r[1])}" for r in top])
                + "\n\nThese companies typically test across multiple areas such as DSA, OOPS, DBMS, system design, and HR communication.\n\n"
                "If you'd like, I can also show you a company-wise preparation plan for any one of them."
            )
            dispatcher.utter_message(text=response)
            return []

        # Complex template variants: best package with lowest CGPA
        if (
            any(k in text for k in ['best package', 'highest package', 'top package', 'high package', 'high packages'])
            and any(k in text for k in ['lowest cgpa', 'low cgpa', 'minimum cgpa', 'lowest cgpa requirement', 'lowest eligibility'])
        ):
            cand = df.copy()
            cand['package_cgpa_ratio'] = cand['max_package_lpa'] / cand['min_cgpa'].replace(0, 1)
            top = cand.sort_values(['package_cgpa_ratio', 'max_package_lpa'], ascending=[False, False])[['company_name', 'max_package_lpa', 'min_cgpa', 'package_cgpa_ratio']].head(5).values.tolist()

            response = (
                "You asked which companies offer the best package with lower CGPA requirements.\n\n"
                "Based on the placement dataset, strong package-to-CGPA options include:\n\n"
                + "\n".join([f"• {r[0]} - Max package: {r[1]:.2f} LPA | Min CGPA: {r[2]:.2f} | Package/CGPA score: {r[3]:.2f}" for r in top])
                + "\n\nThese companies provide a better salary upside relative to their CGPA threshold.\n\n"
                "If you'd like, I can also rank these by interview rounds to find faster hiring paths."
            )
            dispatcher.utter_message(text=response)
            return []

        # Complex template variants: high package with short interview process
        if (
            any(k in text for k in ['high package', 'high packages', 'best package', 'highest package'])
            and any(k in text for k in ['short interview', 'short interviews', 'short interview process', 'short interview processes', 'fewer interview rounds', 'less interview rounds', 'shorter interview'])
        ):
            cand = df.copy()
            cand['short_process_score'] = cand['max_package_lpa'] - (cand['round_count'] * 1.5)
            top = cand.sort_values(['short_process_score', 'max_package_lpa'], ascending=[False, False])[['company_name', 'max_package_lpa', 'round_count']].head(5).values.tolist()

            response = (
                "You asked which companies combine high packages with shorter interview processes.\n\n"
                "According to the placement dataset, good options include:\n\n"
                + "\n".join([f"• {r[0]} - Max package: {r[1]:.2f} LPA | Interview rounds: {int(r[2])}" for r in top])
                + "\n\nThese companies offer stronger salary potential while keeping the interview pipeline relatively shorter."
            )
            dispatcher.utter_message(text=response)
            return []

        # Complex template variants: strong DSA + system design preparation
        if (
            ('dsa' in text and 'system design' in text)
            and any(k in text for k in ['require', 'required', 'strong', 'preparation', 'prepare', 'prep'])
        ):
            filt = df[
                df['required_skills'].astype(str).str.lower().str.contains('dsa|data structures', regex=True, na=False)
                & df['required_skills'].astype(str).str.lower().str.contains('system|design', regex=True, na=False)
            ]
            if filt.empty:
                filt = df[
                    df['prep_system_design_topics'].astype(str).str.lower().ne('na')
                    & df['prep_dsa_topics'].astype(str).str.lower().ne('na')
                ]
            names = filt['company_name'].head(5).tolist()
            response = (
                "You asked which companies require strong DSA and System Design preparation.\n\n"
                "Based on the placement dataset, companies that commonly expect both include:\n\n"
                + "\n".join([f"• {c}" for c in names])
                + "\n\nThese companies usually evaluate both coding depth and architecture thinking in technical rounds."
            )
            dispatcher.utter_message(text=response)
            return []

        # Complex template variants: best for CSE students with a specific CGPA
        if (
            any(k in text_normalized for k in ['best for cse students', 'for cse students', 'cse students with'])
            and 'cgpa' in text
        ):
            cgpa = _extract_number(text, 7.0)
            dept_mask = df['allowed_departments'].astype(str).str.lower().str.contains('cse|cs|computer science|it|all', regex=True, na=False)
            cand = df[dept_mask & (df['min_cgpa'] <= cgpa)].copy()
            if cand.empty:
                cand = df[dept_mask].copy()
            cand['fit_score'] = (cand['avg_package_lpa'] * 1.3) + cand['hiring_intensity'] - (cand['round_count'] * 0.7) - abs(cand['min_cgpa'] - cgpa)
            top = cand.sort_values('fit_score', ascending=False)[['company_name', 'avg_package_lpa', 'min_cgpa', 'round_count']].head(5).values.tolist()
            response = (
                f"You asked which companies are best for CSE students with around {cgpa:.2f} CGPA.\n\n"
                "According to the placement dataset, suitable options include:\n\n"
                + "\n".join([f"• {r[0]} - Avg package: {r[1]:.2f} LPA | Min CGPA: {r[2]:.2f} | Rounds: {int(r[3])}" for r in top])
                + "\n\nThis ranking balances eligibility, package potential, and interview complexity for a CSE profile."
            )
            dispatcher.utter_message(text=response)
            return []

        dispatcher.utter_message(text="Please ask one of the template-based queries on hiring intensity, comparison, recommendation, strategy, advanced filters, or ranking.")
        return []

# ==================== STUDENT-SPECIFIC ACTIONS ====================

class ActionHandleStudentId(Action):
    def name(self) -> Text:
        return "action_handle_student_id"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Try multiple ways to extract student ID
        
        # Method 1: Extract from message text (e.g., "my id is 200001")
        text = tracker.latest_message.get('text', '')
        import re
        
        id_patterns = [
            r'(?:my\s+id|id|student\s+id)[\s:]*(\d+)',
            r'i\s+(?:am|\'m)\s+(\d+)',
            r'^(\d+)$',
        ]
        
        student_id = None
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                student_id = match.group(1)
                break
        
        # Method 2: Extract from sender (sent by Flask backend)
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                student_id = sender
                print(f"[DEBUG] Extracted student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Could not extract student ID. Please provide your ID in the format: 'My ID is 200001'")
            return []
        
        # Validate student ID exists in database
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data. Please try again.")
            return [SlotSet("student_id", student_id)]
        
        # Check if student ID exists
        matching_students = pred_df[pred_df['student_id'].astype(str) == student_id]
        if matching_students.empty:
            dispatcher.utter_message(text=f"Student ID {student_id} not found. Please check and try again.")
            return [SlotSet("student_id", None)]
        
        dispatcher.utter_message(text=f"Great! I've registered your student ID {student_id}. Now you can ask about your placement predictions, profile, or recommended companies.")
        print(f"[DEBUG] Student ID registered: {student_id}")
        return [SlotSet("student_id", student_id)]

class ActionActivateStudentSession(Action):
    def name(self) -> Text:
        return "action_activate_student_session"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """Automatically set student_id from sender if not already set"""
        current_student_id = tracker.get_slot("student_id")
        
        # If student_id is already set, don't override it
        if current_student_id:
            print(f"[DEBUG] Student ID already set: {current_student_id}")
            return []
        
        # Try to extract from sender (Flask sends sender as student_id)
        sender = tracker.sender_id
        if sender and sender.isdigit():
            print(f"[DEBUG] Auto-activated student session for: {sender}")
            return [SlotSet("student_id", sender)]
        
        return []

class ActionGetStudentPlacementProbability(Action):
    def name(self) -> Text:
        return "action_get_student_placement_probability"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                student_id = sender
                print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(
                text=(
                    "Your placement probability needs to be updated before I can answer this query.\n"
                    "Please go to the Placement Prediction Model page and generate/update your prediction, then try again.\n"
                    "[[PREDICTION_UPDATE_REQUIRED]]"
                )
            )
            return []
        
        row = matching.iloc[0]
        try:
            # Important: value is already in percentage in CSV, do not multiply.
            prob = float(row.get('overall_placement_probability', 0))
            role = str(row.get('predicted_job_role', 'N/A'))
            expected_salary = float(row.get('predicted_salary_lpa', 0))
            salary_min = float(row.get('salary_range_min_lpa', 0))
            salary_max = float(row.get('salary_range_max_lpa', 0))
            companies_raw = str(row.get('recommended_companies', '')).strip()
            companies = [c.strip() for c in companies_raw.split(',') if c.strip()]
            companies_text = ", ".join(companies[:6]) if companies else "no specific companies"

            if prob <= 20:
                level = "Very Low"
            elif prob <= 40:
                level = "Low"
            elif prob <= 60:
                level = "Moderate"
            elif prob <= 80:
                level = "Good"
            else:
                level = "Very Strong"

            response = (
                "Based on the current prediction model, your estimated placement probability is:\n\n"
                f"{prob:.1f}%\n\n"
                f"This means that, according to the available data and model analysis, you currently have a {level.lower()} chance of getting placed.\n\n"
                "Why the probability looks like this:\n\n"
                f"- The model predicts that you are most likely to be placed in the role of: {role}.\n"
                f"- Your expected salary is around {expected_salary:.2f} LPA, with a possible range between {salary_min:.2f} and {salary_max:.2f} LPA.\n"
                f"- Based on your profile, companies such as {companies_text} are considered suitable matches.\n\n"
                "Please note that this is only a prediction generated by the model based on historical data and patterns. "
                "Actual placement outcomes may vary depending on interviews, skill development, and company requirements."
            )

            if prob <= 20:
                response += (
                    "\n\nAt the moment, the model indicates a relatively low chance of placement. "
                    "This does not mean placement is impossible - it simply reflects the current prediction based on the available data.\n\n"
                    "Improving technical skills, projects, and interview preparation can significantly increase your chances."
                )
        except Exception as e:
            response = f"Unable to calculate placement probability. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]

class ActionGetStudentPlacementStatus(Action):
    def name(self) -> Text:
        return "action_get_student_placement_status"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                student_id = sender
                print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(
                text=(
                    "Your placement probability needs to be updated before I can answer this query.\n"
                    "Please go to the Placement Prediction Model page and generate/update your prediction, then try again.\n"
                    "[[PREDICTION_UPDATE_REQUIRED]]"
                )
            )
            return []
        
        row = matching.iloc[0]
        try:
            prob = float(row.get('overall_placement_probability', 0))
            if prob >= 81:
                status = "✅ Highly Likely to be Placed"
            elif prob >= 61:
                status = "🟡 Moderately Likely to be Placed"
            elif prob >= 41:
                status = "⚠️ Uncertain - Needs Improvement"
            else:
                status = "❌ Currently at Risk"
            
            response = f"Your placement status: {status}\n\nPlacement Probability: {prob:.1f}%"
        except:
            response = "Unable to determine placement status."
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentPredictedCompany(Action):
    def name(self) -> Text:
        return "action_get_student_predicted_company"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(text="I'm sorry, but I could not find company recommendation data for your student ID.\n\nPlease check the ID or contact the placement cell.")
            return []
        
        row = matching.iloc[0]
        try:
            companies_str = str(row.get('recommended_companies', '')).strip()
            role = str(row.get('predicted_job_role', 'N/A'))
            salary_prediction = float(row.get('predicted_salary_lpa', 0))
            salary_min = float(row.get('salary_range_min_lpa', 0))
            salary_max = float(row.get('salary_range_max_lpa', 0))
            placement_probability = float(row.get('overall_placement_probability', 0))

            if companies_str:
                response = (
                    "Based on the current prediction model, the following companies are considered good matches for your profile:\n\n"
                    f"Recommended companies:\n{companies_str}\n\n"
                    "Why these companies are suggested:\n\n"
                    f"- The model predicts that you are most likely to be placed in the role of {role}.\n"
                    f"- Your expected salary is around {salary_prediction:.2f} LPA, with a possible range between {salary_min:.2f} and {salary_max:.2f} LPA.\n"
                    "- Companies in this list typically recruit candidates for similar roles and salary ranges.\n"
                    f"- Your current placement probability is estimated to be {placement_probability:.1f}%.\n\n"
                    "Please note that these recommendations are based on historical placement data and model predictions. "
                    "Actual hiring depends on company requirements, interview performance, and available openings."
                )
            else:
                response = (
                    "Company recommendations for your profile are not currently available in the system.\n\n"
                    "Please check again later or contact the placement office for assistance."
                )
        except Exception as e:
            response = f"Unable to retrieve company recommendations. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentPredictedJobRole(Action):
    def name(self) -> Text:
        return "action_get_student_predicted_job_role"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == student_id]
        if matching.empty:
            dispatcher.utter_message(text="No data found for your student ID.")
            return []
        
        row = matching.iloc[0]
        try:
            role = row.get('predicted_job_role', 'Software Engineer')
            response = f"The predicted job role for you is: **{role}**"
        except:
            response = "Unable to retrieve job role prediction."
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentPredictedSalary(Action):
    def name(self) -> Text:
        return "action_get_student_predicted_salary"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(text="I'm sorry, but I could not find salary prediction data for your student ID.\nPlease check the ID or contact the placement office.")
            return []
        
        row = matching.iloc[0]
        try:
            predicted_salary = float(row.get('predicted_salary_lpa', 0))
            salary_min = float(row.get('salary_range_min_lpa', 0))
            salary_mid = float(row.get('salary_range_mid_lpa', 0))
            salary_max = float(row.get('salary_range_max_lpa', 0))
            job_role = str(row.get('predicted_job_role', 'N/A'))
            companies = str(row.get('recommended_companies', '')).strip()
            prob_gt_5 = float(row.get('prob_salary_gt_5_lpa', 0))
            prob_gt_10 = float(row.get('prob_salary_gt_10_lpa', 0))
            prob_gt_15 = float(row.get('prob_salary_gt_15_lpa', 0))

            if predicted_salary <= 0 and salary_max <= 0:
                response = (
                    "Your salary prediction has not yet been generated in the system.\n\n"
                    "Please check again later or contact the placement cell for more information."
                )
            else:
                response = (
                    "Based on the current prediction model, your estimated salary after placement is around:\n\n"
                    f"{predicted_salary:.2f} LPA\n\n"
                    "Expected salary range:\n"
                    f"Between {salary_min:.2f} LPA and {salary_max:.2f} LPA.\n\n"
                    "Why this salary is predicted:\n\n"
                    f"- The model estimates that you are most likely to be placed in the role of {job_role}.\n"
                    "- For this role, the typical salary range observed in past placement data is within the predicted range.\n"
                    f"- Companies such as {companies if companies else 'the recommended recruiters'} are considered suitable matches for your profile.\n\n"
                    "Salary probability insights:\n\n"
                    f"- Probability of getting more than 5 LPA: {prob_gt_5:.1f}%\n"
                    f"- Probability of getting more than 10 LPA: {prob_gt_10:.1f}%\n"
                    f"- Probability of getting more than 15 LPA: {prob_gt_15:.1f}%\n\n"
                    "Please note that this is a prediction generated using historical placement data and machine learning models. "
                    "Actual salary offers may vary depending on interview performance, company hiring patterns, and market conditions."
                )
                
        except Exception as e:
            response = f"Unable to retrieve salary prediction. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentProfileSummary(Action):
    def name(self) -> Text:
        return "action_get_student_profile_summary"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == student_id]
        if matching.empty:
            dispatcher.utter_message(text="No data found for your student ID.")
            return []
        
        row = matching.iloc[0]
        try:
            prob = float(row.get('overall_placement_probability', 0))
            role = row.get('predicted_job_role', 'Software Engineer')
            min_salary = float(row.get('salary_range_min_lpa', 0))
            max_salary = float(row.get('salary_range_max_lpa', 0))
            companies_str = row.get('recommended_companies', 'N/A')
            
            # Get top company
            top_company = companies_str.split(',')[0].strip() if companies_str and companies_str != 'N/A' else 'TBD'
            
            # Determine status emoji
            if prob >= 90:
                status_emoji = "🟢"
            elif prob >= 50:
                status_emoji = "🟡"
            else:
                status_emoji = "🔴"
            
            summary = (
                f"📋 **Your Complete Profile Summary**\n\n"
                f"👤 **Student ID:** {student_id}\n\n"
                f"📊 **Placement Metrics:**\n"
                f"• Placement Probability: {prob:.1f}% {status_emoji}\n"
                f"• Predicted Role: **{role}**\n"
                f"• Top Company Match: **{top_company}**\n\n"
                f"💰 **Salary Expectations:**\n"
                f"• Expected Range: {min_salary:.1f} - {max_salary:.1f} LPA\n\n"
                f"🎯 **Recommendations:**\n"
                f"1. Focus on companies in your recommended list\n"
                f"2. Prepare for {role} role-specific questions\n"
                f"3. Work on technical skills and communication\n"
                f"4. Keep your academic performance strong"
            )
            response = summary
        except Exception as e:
            response = f"Unable to retrieve profile summary: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentAreasToImprove(Action):
    def name(self) -> Text:
        return "action_get_student_areas_to_improve"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        response = (
            "📚 Areas to Improve:\n\n"
            "Based on our analysis, focus on:\n"
            "1. **Data Structures & Algorithms** - Practice on LeetCode\n"
            "2. **System Design** - Learn architecture basics\n"
            "3. **Communication Skills** - Practice mock interviews\n"
            "4. **Project Work** - Build real-world projects"
        )
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetStudentCompanyFit(Action):
    def name(self) -> Text:
        return "action_get_student_company_fit"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        # Auto-activate from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
                        print(f"[DEBUG] Auto-activated student_id from sender: {student_id}")
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        # Get company from context if available
        company, _ = resolve_company(tracker)
        if not company:
            dispatcher.utter_message(text="Which company's fit would you like to check?")
            return []
        
        pred_df = DataStore.get_predictions_df()
        df = DataStore.get_df()
        
        if pred_df.empty or df.empty:
            dispatcher.utter_message(text="Unable to load data.")
            return []
        
        try:
            student_match = pred_df[pred_df['student_id'].astype(str) == student_id]
            company_match = df[df['company_name'] == company]
            
            if student_match.empty or company_match.empty:
                dispatcher.utter_message(text="Data not available for this query.")
                return []
            
            response = f"🎯 Your Fit with {company}:\n\n✅ Your profile shows a good match with this company.\n\nRecommended preparation areas: DSA, System Design, Communication Skills"
        except:
            response = "Unable to calculate company fit."
        
        dispatcher.utter_message(text=response)
        return []

# ==================== NEW STUDENT ACTIONS - SALARY ANALYSIS ====================

class ActionGetSalaryRange(Action):
    def name(self) -> Text:
        return "action_get_salary_range"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(text="I'm sorry, but I could not find salary range prediction data for your student ID.\nPlease check the ID or contact the placement office.")
            return []
        
        row = matching.iloc[0]
        try:
            min_salary = float(row.get('salary_range_min_lpa', 0))
            max_salary = float(row.get('salary_range_max_lpa', 0))
            mid_salary = float(row.get('salary_range_mid_lpa', 0))
            
            response = (
                "Based on the current prediction model, your expected salary range during placements is:\n\n"
                f"Minimum expected salary: {min_salary:.2f} LPA\n"
                f"Most likely salary (mid estimate): {mid_salary:.2f} LPA\n"
                f"Maximum possible salary: {max_salary:.2f} LPA\n\n"
                "Why this range is predicted:\n\n"
                f"- The model predicts that you are most likely to be placed in the role of {str(row.get('predicted_job_role', 'N/A'))}.\n"
                "- Based on historical placement data for similar profiles, salary offers for this role typically fall within this range.\n"
                f"- Companies such as {str(row.get('recommended_companies', 'the recommended recruiters'))} are considered good matches for your profile and usually offer salaries within this bracket.\n\n"
                "Please note that this is an estimated range generated by the prediction model. Actual salary offers may vary depending on company hiring patterns, interview performance, and market conditions."
            )
        except Exception as e:
            response = f"Unable to calculate salary range. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetSalaryThresholdProbability(Action):
    def name(self) -> Text:
        return "action_get_salary_threshold"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(text="No data found for your student ID.")
            return []
        
        row = matching.iloc[0]
        try:
            # Get all probability thresholds
            thresholds = {
                "2 LPA": float(row.get('prob_salary_gt_2_lpa', 0)),
                "5 LPA": float(row.get('prob_salary_gt_5_lpa', 0)),
                "10 LPA": float(row.get('prob_salary_gt_10_lpa', 0)),
                "15 LPA": float(row.get('prob_salary_gt_15_lpa', 0)),
                "20 LPA": float(row.get('prob_salary_gt_20_lpa', 0)),
                "25 LPA": float(row.get('prob_salary_gt_25_lpa', 0)),
                "30 LPA": float(row.get('prob_salary_gt_30_lpa', 0)),
            }
            
            response = "💼 **Your Salary Threshold Probabilities:**\n\n"
            response += "Chances of getting above specific salary levels:\n\n"
            
            for threshold, prob in thresholds.items():
                # Values are already percentages in CSV.
                prob_pct = prob
                # Create progress indicator
                if prob_pct >= 80:
                    indicator = "🟢 Very Likely"
                elif prob_pct >= 50:
                    indicator = "🟡 Likely"
                elif prob_pct >= 20:
                    indicator = "🟠 Possible"
                else:
                    indicator = "🔴 Unlikely"
                
                response += f"• Above **{threshold}**: {prob_pct:.1f}% {indicator}\n"
            
            response += (
                f"\n💡 **Interpretation:**\n"
                f"These probabilities help you understand the likelihood of different salary brackets. "
                f"Focus on companies and roles that align with your higher probability ranges."
            )
        except Exception as e:
            response = f"Unable to calculate salary thresholds. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionGetPlacementAndSalary(Action):
    def name(self) -> Text:
        return "action_get_placement_and_salary"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id = tracker.get_slot("student_id")
        
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                pred_df = DataStore.get_predictions_df()
                if not pred_df.empty:
                    matching = pred_df[pred_df['student_id'].astype(str) == sender]
                    if not matching.empty:
                        student_id = sender
        
        if not student_id:
            dispatcher.utter_message(text="Please provide your student ID first.")
            return []
        
        pred_df = DataStore.get_predictions_df()
        if pred_df.empty:
            dispatcher.utter_message(text="Unable to load student data.")
            return []
        
        matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
        if matching.empty:
            dispatcher.utter_message(text="No data found for your student ID.")
            return []
        
        row = matching.iloc[0]
        try:
            prob = float(row.get('overall_placement_probability', 0))
            min_salary = float(row.get('salary_range_min_lpa', 0))
            max_salary = float(row.get('salary_range_max_lpa', 0))
            mid_salary = float(row.get('salary_range_mid_lpa', 0))
            role = row.get('predicted_job_role', 'Software Engineer')
            
            # Generate combined assessment
            if prob >= 85:
                placement_outlook = "Excellent! You have outstanding placement chances."
            elif prob >= 60:
                placement_outlook = "Good! You have strong placement prospects."
            elif prob >= 40:
                placement_outlook = "Fair. You have moderate placement chances."
            else:
                placement_outlook = "Challenging. You need to focus on improvement."
            
            if mid_salary >= 15:
                salary_outlook = "You can expect premium compensation."
            elif mid_salary >= 8:
                salary_outlook = "You can expect competitive mid-range compensation."
            else:
                salary_outlook = "You can expect entry-level starting salary."
            
            response = (
                f"📊 **Your Complete Placement & Salary Analysis:**\n\n"
                f"🎯 **Placement Outlook:**\n"
                f"{placement_outlook} Probability: {prob:.1f}%\n\n"
                f"💰 **Salary Outlook:**\n"
                f"{salary_outlook}\n"
                f"• Expected Range: {min_salary:.1f} - {max_salary:.1f} LPA\n"
                f"• Mid-salary Prediction: {mid_salary:.1f} LPA\n\n"
                f"👔 **Expected Role:**\n"
                f"**{role}**\n\n"
                f"✅ **Action Plan:**\n"
                f"1. Focus on interview preparation for {role} position\n"
                f"2. Target companies offering {mid_salary:.1f}+ LPA\n"
                f"3. Practice negotiation skills\n"
                f"4. Build a strong portfolio"
            )
        except Exception as e:
            response = f"Unable to retrieve complete analysis. Error: {str(e)}"
        
        dispatcher.utter_message(text=response)
        return []

# ==================== NEW MULTI-INTENT ACTIONS ====================

def _student_context_from_tracker(tracker: Tracker) -> Tuple[Optional[str], Optional[pd.Series], Optional[str]]:
    """Resolve student id from slot/sender and fetch the prediction row."""
    student_id = tracker.get_slot("student_id")
    pred_df = DataStore.get_predictions_df()

    if pred_df.empty:
        return None, None, "Unable to load student prediction data right now. Please try again."

    if not student_id:
        sender = tracker.sender_id
        if sender and sender.isdigit():
            match = pred_df[pred_df['student_id'].astype(str) == sender]
            if not match.empty:
                student_id = sender

    if not student_id:
        return None, None, "Please provide your student ID first."

    matching = pred_df[pred_df['student_id'].astype(str) == str(student_id)]
    if matching.empty:
        return str(student_id), None, "I'm sorry, but I could not find prediction data for your student ID. Please check the ID or contact the placement cell."

    return str(student_id), matching.iloc[0], None


def _companies_text(raw_companies: Any, limit: int = 6) -> str:
    raw = str(raw_companies or "").strip()
    if not raw:
        return "Not available"
    seen = set()
    out = []
    for c in [x.strip() for x in raw.split(',') if x.strip()]:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            out.append(c)
    return ", ".join(out[:limit]) if out else "Not available"


def _extract_threshold_from_text(text: str) -> Optional[int]:
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*lpa', text.lower())
    if matches:
        return int(float(matches[0]))
    nums = re.findall(r'\b(5|10|15|20|25|30|35|40)\b', text)
    if nums:
        return int(nums[0])
    return None


def _prob_column_for_threshold(threshold: int) -> Optional[str]:
    mapping = {
        2: 'prob_salary_gt_2_lpa',
        5: 'prob_salary_gt_5_lpa',
        10: 'prob_salary_gt_10_lpa',
        15: 'prob_salary_gt_15_lpa',
        20: 'prob_salary_gt_20_lpa',
        25: 'prob_salary_gt_25_lpa',
        30: 'prob_salary_gt_30_lpa',
        35: 'prob_salary_gt_35_lpa',
        40: 'prob_salary_gt_40_lpa',
    }
    return mapping.get(threshold)


class ActionGetPlacementSummary(Action):
    def name(self) -> Text:
        return "action_get_placement_summary"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        placement_probability = float(row.get('overall_placement_probability', 0))
        predicted_salary = float(row.get('predicted_salary_lpa', 0))
        salary_min = float(row.get('salary_range_min_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        salary_max = float(row.get('salary_range_max_lpa', 0))
        job_role = str(row.get('predicted_job_role', 'Not available'))
        companies = _companies_text(row.get('recommended_companies', ''))

        response = (
            "Here is a summary of your placement prediction based on the current model:\n\n"
            f"Placement probability:\n{placement_probability:.1f}%\n\n"
            f"Predicted job role:\n{job_role}\n\n"
            f"Expected salary:\nAround {predicted_salary:.2f} LPA\n\n"
            "Estimated salary range:\n"
            f"Between {salary_min:.2f} LPA and {salary_max:.2f} LPA.\n\n"
            f"Recommended companies:\n{companies}\n\n"
            "Explanation:\n\n"
            f"- The model predicts that your profile aligns most closely with the role of {job_role}.\n"
            "- Based on similar placement data from previous years, candidates in this role usually receive salary offers within the predicted range.\n"
            "- Companies listed above frequently recruit for this role and salary bracket.\n\n"
            "Please note that these results are predictions based on historical placement patterns and model analysis. "
            "Actual outcomes may vary depending on interviews, skills, and company hiring conditions."
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]


class ActionGetPlacementAnalytical(Action):
    def name(self) -> Text:
        return "action_get_placement_analytical"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        text = (tracker.latest_message.get('text', '') or '').lower()
        placement_probability = float(row.get('overall_placement_probability', 0))
        salary_min = float(row.get('salary_range_min_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        salary_max = float(row.get('salary_range_max_lpa', 0))
        predicted_salary = float(row.get('predicted_salary_lpa', 0))
        role = str(row.get('predicted_job_role', 'Not available'))
        companies = _companies_text(row.get('recommended_companies', ''), limit=8)

        threshold = _extract_threshold_from_text(text)
        if threshold:
            col = _prob_column_for_threshold(threshold)
            if col and col in row.index:
                prob_at_threshold = float(row.get(col, 0))
                response = (
                    f"Your overall placement probability is {placement_probability:.1f}%.\n\n"
                    f"Among those placements, the probability of receiving a salary above {threshold} LPA is estimated to be {prob_at_threshold:.1f}%.\n\n"
                    f"This means that while your overall chance of getting placed is {placement_probability:.1f}%, "
                    f"the likelihood of receiving a package above {threshold} LPA depends on company selection and role demand.\n\n"
                    f"The model predicts that your most likely role is {role}, where salaries typically fall between {salary_min:.2f} and {salary_max:.2f} LPA."
                )
                dispatcher.utter_message(text=response)
                return [SlotSet("student_id", student_id)]

        if "most likely salary" in text or "if i get placed" in text:
            response = (
                "If you get placed, the most likely salary based on the prediction model is around:\n\n"
                f"{salary_mid:.2f} LPA\n\n"
                "This value represents the midpoint of the predicted salary range.\n\n"
                f"Your full predicted salary range is between {salary_min:.2f} LPA and {salary_max:.2f} LPA.\n\n"
                "This estimate is based on historical placement outcomes for candidates with similar profiles."
            )
            dispatcher.utter_message(text=response)
            return [SlotSet("student_id", student_id)]

        if "which companies" in text and "salary range" in text:
            response = (
                f"Based on your predicted salary range of {salary_min:.2f} to {salary_max:.2f} LPA, the following companies are considered suitable matches:\n\n"
                f"{companies}\n\n"
                f"These companies typically recruit candidates for the role of {role} and offer packages within the predicted salary range.\n\n"
                "However, actual offers depend on interview performance and current company hiring policies."
            )
            dispatcher.utter_message(text=response)
            return [SlotSet("student_id", student_id)]

        response = (
            "Based on your current prediction data:\n\n"
            f"- Placement probability: {placement_probability:.1f}%\n"
            f"- Most likely role: {role}\n"
            f"- Most likely salary: {predicted_salary:.2f} LPA\n"
            f"- Salary range: {salary_min:.2f} to {salary_max:.2f} LPA\n"
            f"- Recommended companies: {companies}\n\n"
            "This analytical estimate is based on historical placement patterns for similar profiles."
        )
        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]


class ActionGetSalaryComparison(Action):
    def name(self) -> Text:
        return "action_get_salary_comparison"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        text = (tracker.latest_message.get('text', '') or '').lower()
        salary_min = float(row.get('salary_range_min_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        salary_max = float(row.get('salary_range_max_lpa', 0))

        if "difference" in text and ("minimum" in text or "maximum" in text or "range" in text):
            diff = salary_max - salary_min
            response = (
                f"Your predicted salary range is between {salary_min:.2f} LPA and {salary_max:.2f} LPA.\n\n"
                "The difference between the minimum and maximum predicted salary is:\n\n"
                f"{diff:.2f} LPA.\n\n"
                "This range reflects the variation in salary offers depending on the company and role."
            )
            dispatcher.utter_message(text=response)
            return [SlotSet("student_id", student_id)]

        thresholds = re.findall(r'\b(5|10|15|20)\b', text)
        if len(thresholds) >= 2:
            t1 = int(thresholds[0])
            t2 = int(thresholds[1])
            c1 = _prob_column_for_threshold(t1)
            c2 = _prob_column_for_threshold(t2)
            p1 = float(row.get(c1, 0)) if c1 else 0.0
            p2 = float(row.get(c2, 0)) if c2 else 0.0
            higher = f"{t1} LPA" if p1 >= p2 else f"{t2} LPA"
            response = (
                "Based on the prediction model:\n\n"
                f"- Probability of getting more than {t1} LPA: {p1:.1f}%\n"
                f"- Probability of getting more than {t2} LPA: {p2:.1f}%\n\n"
                f"This means it is more likely that you will receive a salary above {higher}.\n\n"
                "This estimate is based on historical placement outcomes for similar profiles."
            )
            dispatcher.utter_message(text=response)
            return [SlotSet("student_id", student_id)]

        response = (
            "Based on the prediction model, the salary bracket you are most likely to fall into is around:\n\n"
            f"{salary_mid:.2f} LPA.\n\n"
            f"Your full predicted salary range is between {salary_min:.2f} and {salary_max:.2f} LPA.\n\n"
            "This estimate is based on historical placement outcomes for candidates with similar profiles."
        )
        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]


class ActionGetPlacementAdvice(Action):
    def name(self) -> Text:
        return "action_get_placement_advice"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        placement_probability = float(row.get('overall_placement_probability', 0))
        predicted_salary = float(row.get('predicted_salary_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        role = str(row.get('predicted_job_role', 'Not available'))
        companies = _companies_text(row.get('recommended_companies', ''), limit=8)
        prob_gt_10 = float(row.get('prob_salary_gt_10_lpa', 0))
        prob_gt_15 = float(row.get('prob_salary_gt_15_lpa', 0))

        if prob_gt_15 > 50:
            suggestion = "Your profile currently supports targeting high paying companies, while still keeping a few balanced options as backup."
        elif prob_gt_10 >= 30:
            suggestion = "A balanced strategy is recommended: apply to a mix of product and service companies to maximize opportunities."
        else:
            suggestion = "At this stage, it may be better to prioritize service and mid-range companies first, while continuing to improve for higher-paying targets."

        response = (
            "Based on your current prediction:\n\n"
            f"- Placement probability: {placement_probability:.1f}%\n"
            f"- Expected salary: around {predicted_salary:.2f} LPA\n"
            f"- Most likely salary (mid): {salary_mid:.2f} LPA\n\n"
            f"Your most likely role is predicted to be: {role}.\n\n"
            f"Companies that match your profile include:\n{companies}\n\n"
            "Suggestion:\n\n"
            f"{suggestion}\n\n"
            "Please remember that this advice is based on prediction data, and actual outcomes depend on skills, interview performance, and company hiring conditions."
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]


class ActionGetPlacementExplanation(Action):
    def name(self) -> Text:
        return "action_get_placement_explanation"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        placement_probability = float(row.get('overall_placement_probability', 0))
        predicted_salary = float(row.get('predicted_salary_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        role = str(row.get('predicted_job_role', 'Not available'))
        companies = _companies_text(row.get('recommended_companies', ''), limit=6)

        response = (
            "Your current placement prediction is based on the following factors:\n\n"
            f"- Predicted job role: {role}\n"
            f"- Expected salary: around {predicted_salary:.2f} LPA\n"
            f"- Most likely salary (mid): {salary_mid:.2f} LPA\n"
            f"- Placement probability: {placement_probability:.1f}%\n\n"
            "These predictions are generated using patterns observed in historical placement data for similar profiles.\n\n"
            "Ways to improve your placement chances may include:\n\n"
            "- Strengthening technical skills related to your predicted role\n"
            "- Practicing interview preparation\n"
            f"- Applying to companies that match your profile, such as: {companies}\n\n"
            "Please remember that predictions are estimates and can improve with preparation and skill development."
        )

        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]


class ActionGetRealisticStudentResponse(Action):
    def name(self) -> Text:
        return "action_get_realistic_student_response"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        student_id, row, err = _student_context_from_tracker(tracker)
        if err:
            dispatcher.utter_message(text=err)
            return []

        text = (tracker.latest_message.get('text', '') or '').lower()
        placement_probability = float(row.get('overall_placement_probability', 0))
        predicted_salary = float(row.get('predicted_salary_lpa', 0))
        salary_mid = float(row.get('salary_range_mid_lpa', 0))
        salary_max = float(row.get('salary_range_max_lpa', 0))
        prob_gt_10 = float(row.get('prob_salary_gt_10_lpa', 0))
        prob_gt_15 = float(row.get('prob_salary_gt_15_lpa', 0))
        companies = _companies_text(row.get('recommended_companies', ''), limit=8)
        role = str(row.get('predicted_job_role', 'Not available'))

        if "10 lpa" in text:
            response = (
                "According to the prediction model:\n\n"
                f"Your probability of receiving a salary above 10 LPA is estimated to be {prob_gt_10:.1f}%.\n\n"
                f"Your most likely predicted salary is around {salary_mid:.2f} LPA.\n\n"
                "While getting a 10 LPA package is possible, it will depend on the company you apply to and your interview performance."
            )
        elif "high package" in text or "high paying" in text:
            response = (
                f"Based on your current prediction, your probability of crossing 15 LPA is {prob_gt_15:.1f}%.\n\n"
                f"Your expected salary is around {predicted_salary:.2f} LPA, with upper outcomes up to {salary_max:.2f} LPA.\n\n"
                "A high package is possible, but it usually requires strong interview performance and applying to the right companies."
            )
        elif "which companies" in text or "realistically" in text:
            response = (
                "Based on the current prediction model, companies that are considered suitable matches for your profile include:\n\n"
                f"{companies}\n\n"
                f"These companies typically recruit candidates for the role of {role} and offer salaries within your predicted range."
            )
        else:
            response = (
                "Your predicted placement probability is currently:\n\n"
                f"{placement_probability:.1f}%.\n\n"
                "This means there is a reasonable chance of getting placed based on the current prediction model.\n\n"
                "However, placement outcomes also depend on interview performance, preparation, and company hiring conditions."
            )

        dispatcher.utter_message(text=response)
        return [SlotSet("student_id", student_id)]

# ==================== UTILITY ====================

class ActionListCompaniesByBranch(Action):
    def name(self) -> Text:
        return "action_list_companies_by_branch"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()
        
        branch = None
        if 'cs' in user_text or 'computer science' in user_text:
            branch = 'CS'
        elif 'it' in user_text or 'information technology' in user_text:
            branch = 'IT'
        elif 'ece' in user_text or 'electronics' in user_text:
            branch = 'ECE'
        elif 'ee' in user_text or 'electrical' in user_text:
            branch = 'EE'
        
        if not branch:
            dispatcher.utter_message(text="Which branch? (e.g., 'Companies for CS students')")
            return []
        
        filtered = df[df['allowed_departments'].str.contains(branch, case=False, na=False)]
        companies = filtered['company_name'].tolist()
        
        if companies:
            response = f"Companies for {branch} students ({len(companies)} total):\n" + "\n".join([f"- {c}" for c in companies[:20]])
        else:
            response = f"No companies found for {branch} branch."
        
        dispatcher.utter_message(text=response)
        return []

class ActionListCompaniesByCategory(Action):
    def name(self) -> Text:
        return "action_list_companies_by_category"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()

        if 'easy' in user_text or 'easiest' in user_text or 'accessible' in user_text:
            sorted_df = df.sort_values('difficulty_factor', ascending=True)
            data = sorted_df[['company_name', 'difficulty_factor']].values.tolist()
            response = ("Companies with the easiest hiring processes (sorted by difficulty):\n" +
                        "\n".join([f"- {r[0]} (difficulty: {r[1]}/10)" for r in data[:15]]))
        elif 'product' in user_text:
            filtered = df[df['company_cat'].str.lower().str.contains('product', na=False)]
            companies = filtered['company_name'].tolist()
            response = ((f"Product-based companies ({len(companies)} total):\n" +
                         "\n".join([f"- {c}" for c in companies]))
                        if companies else "No product-based companies found.")
        elif 'service' in user_text:
            filtered = df[df['company_cat'].str.lower().str.contains('service', na=False)]
            companies = filtered['company_name'].tolist()
            response = ((f"Service-based companies ({len(companies)} total):\n" +
                         "\n".join([f"- {c}" for c in companies]))
                        if companies else "No service-based companies found.")
        else:
            companies = df['company_name'].tolist()
            response = (f"All companies in our database ({len(companies)} total):\n" +
                        "\n".join([f"- {c}" for c in companies]))

        dispatcher.utter_message(text=response)
        return []

class ActionCountCompaniesByCriteria(Action):
    def name(self) -> Text:
        return "action_count_companies_by_criteria"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        df = DataStore.get_df()
        user_text = tracker.latest_message.get('text', '').lower()
        
        if 'backlog' in user_text:
            count = len(df[df['backlogs_allowed'].apply(_backlogs_allowed_count) > 0])
            response = f"Number of companies allowing backlogs: {count}"
        elif 'tier' in user_text and '1' in user_text:
            count = len(df[df['company_tier'].str.contains('Tier-1', case=False, na=False)])
            response = f"Number of Tier-1 companies: {count}"
        elif 'cgpa' in user_text:
            import re
            cgpa_match = re.search(r'(\d+\.?\d*)', user_text)
            cgpa = float(cgpa_match.group(1)) if cgpa_match else 7.0
            count = len(df[df['min_cgpa'] <= cgpa])
            response = f"Number of companies accepting CGPA {cgpa}+: {count}"
        else:
            response = f"Total companies in database: {len(df)}"
        
        dispatcher.utter_message(text=response)
        return []

class ActionProvideCompanyOptions(Action):
    def name(self) -> Text:
        return "action_provide_company_options"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Resolve company (expecting entity or fuzzy)
        company, source = resolve_company(tracker)
        
        if not company:
             dispatcher.utter_message(text="Which company are you interested in?")
             return [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        message = f"What would you like to know about {company}?"
        buttons = [
            {"title": "Package", "payload": "package"},
            {"title": "CGPA", "payload": "cgpa"},
            {"title": "Backlog Policy", "payload": "backlog policy"},
            {"title": "Roles", "payload": "roles"},
            {"title": "Interview Process", "payload": "interview process"},
            {"title": "Preparation", "payload": "preparation topics"},
        ]
        dispatcher.utter_message(text=message, buttons=buttons)
        
        # CR-04: Set 'company' (Active), Clear 'last_company_asked' (Context)
        return [SlotSet("company", company), SlotSet("last_company_asked", None)]

# ==================== UTILITY ====================

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        intent = tracker.latest_message.get('intent', {}).get('name', 'unknown')
        raw_text = tracker.latest_message.get('text', '') or ''
        text = raw_text.lower()
        student_id = tracker.get_slot("student_id")
        events: List[Dict[Text, Any]] = []
        
        # FIRST: Try to auto-activate student session from sender if not set
        if not student_id:
            sender = tracker.sender_id
            if sender and sender.isdigit():
                student_id = sender
                print(f"[DEBUG] Auto-activated student session from sender: {student_id}")
                events.append(SlotSet("student_id", student_id))
        
        print(f"[DEBUG] Fallback | Intent: {intent} | Student ID: {student_id}")
        
        # Priority 1: If student ID is not set, prompt for it (for student-specific queries)
        student_intents = [
            'ask_student_placement_probability', 'ask_student_placement_status',
            'ask_student_predicted_company', 'ask_student_predicted_job_role',
            'ask_student_predicted_salary', 'ask_student_profile_summary',
            'ask_student_areas_to_improve', 'ask_student_company_fit',
            'ask_salary_range', 'ask_salary_threshold', 'ask_placement_and_salary',
            'ask_recommended_companies', 'placement_probability_query',
            'salary_prediction_query', 'salary_range_query', 'recommended_companies_query',
            'placement_summary_query', 'placement_analytical_query',
            'salary_comparison_query', 'placement_advice_query',
            'placement_explanation_query', 'realistic_student_query'
        ]

        # Force-route template-heavy queries even when intent classification is noisy.
        companies = _list_leetcode_companies()

        template_triggers = [
            'show companies with', 'rank companies by', 'top ', 'highest paying companies',
            'hiring intensity', 'which is better', 'compare ', 'should i focus on',
            'easier to crack', 'salary vs difficulty ratio', 'high salary and high hiring',
            'good packages but hire many', 'high salary but low hiring',
            'which companies should i target', 'most preparation topics',
            'tier 1 companies offer more than', 'fewer interview rounds',
            'best package with the lowest cgpa requirement', 'high packages and short interview processes',
            'strong dsa and system design preparation', 'best for cse students with',
            'leetcode questions for', 'leetcode report for', 'interview questions for',
            'questions asked by', 'questions from', 'problems asked by',
            'latest questions', 'last 30 days questions', 'last 3 months questions',
            'last 6 months questions', 'last year questions', 'all questions asked by',
            'top interview questions', 'most frequently asked', 'practice for'
        ]
        if _is_leetcode_company_questions_query(tracker, text, companies):
            return events + [FollowupAction('action_handle_template_queries')]

        if any(k in text for k in template_triggers):
            return events + [FollowupAction('action_handle_template_queries')]

        # Keyword routing for nlu_fallback to robustly support common student asks.
        if intent == 'nlu_fallback':
            if any(k in text for k in ['predicted role and salary', 'placement probability and expected salary range', 'placement chances and expected salary']):
                return events + [FollowupAction('action_get_placement_summary')]

            if any(k in text for k in ['if i get placed', 'salary above', 'in recommended companies', 'most likely salary']):
                return events + [FollowupAction('action_get_placement_analytical')]

            if any(k in text for k in ['more likely that i will get above', 'difference between my minimum and maximum salary', 'salary bracket am i most likely']):
                return events + [FollowupAction('action_get_salary_comparison')]

            if any(k in text for k in ['should i target high paying companies', 'top tech companies', 'product companies or service companies', 'should i expect a high salary offer']):
                return events + [FollowupAction('action_get_placement_advice')]

            if any(k in text for k in ['can you explain my salary prediction', 'why is my placement probability low', 'how can i increase my expected salary']):
                return events + [FollowupAction('action_get_placement_explanation')]

            if any(k in text for k in ['will i get placed this year', 'can i get a 10 lpa package', 'which companies can i realistically get into', 'do i have a chance of getting a high package']):
                return events + [FollowupAction('action_get_realistic_student_response')]

            if any(k in text for k in ['placement probability', 'chances of getting placed', 'job chances', 'will i get placed', 'placement chance']):
                return events + [FollowupAction('action_get_student_placement_probability')]

            if any(k in text for k in ['which companies should i apply', 'recommended companies', 'recruiters match', 'companies might hire', 'suitable companies']):
                return events + [FollowupAction('action_get_student_predicted_company')]

            if any(k in text for k in ['salary package', 'predicted salary', 'expected ctc', 'estimated salary offered', 'expected salary']) and 'range' not in text:
                return events + [FollowupAction('action_get_student_predicted_salary')]

            if any(k in text for k in ['salary range', 'minimum salary', 'maximum salary', 'mid salary', 'lowest and highest salary']):
                return events + [FollowupAction('action_get_salary_range')]

            if 'lpa' in text and any(k in text for k in ['above', 'more than', 'chance', 'probability']):
                return events + [FollowupAction('action_get_salary_threshold')]

            if any(k in text for k in ['placement chances and expected salary', 'predicted role and salary', 'placement and salary']):
                return events + [FollowupAction('action_get_placement_and_salary')]

            if _is_leetcode_company_questions_query(tracker, text, companies):
                return events + [FollowupAction('action_handle_template_queries')]

        if not student_id and intent in student_intents:
            dispatcher.utter_message(text="I'm sorry, I can't answer that without knowing who you are. Please provide your student ID to get started (e.g., 'my id is 12345').")
            return events + [SlotSet("student_id", None)]

        # Priority 2: Check if company-specific intent but company missing
        company_intents = [
            'ask_avg_package', 'ask_max_package', 'ask_min_cgpa',
            'ask_allowed_departments', 'ask_required_skills',
            'ask_backlog_allowed', 'ask_max_backlogs',
            'ask_company_tier', 'ask_hiring_roles',
            'ask_eligibility_summary', 'ask_interview_process',
            'ask_preparation_roadmap', 'ask_prep_topics_by_area'
        ]
        if intent in company_intents:
            dispatcher.utter_message(text="Which company are you asking about? Please specify the company name (e.g., 'Google' or 'TCS').")
            return events + [SlotSet("company", None), SlotSet("last_company_asked", None)]
        
        # Priority 3: Generic fallback for a known user
        if student_id:
            dispatcher.utter_message(
                text="I'm sorry, I didn't quite catch that. You can ask me about:\n- Your placement predictions (e.g., 'will I get placed?')\n- Company details (e.g., 'Google package')\n- Your profile (e.g., 'show my summary')"
            )
        else:
            # Fallback for user who hasn't identified themselves
            dispatcher.utter_message(
                text="I'm sorry, I didn't quite catch that. Please start by providing your student ID. Or you can ask about general company information (e.g., 'Tell me about Google')."
            )
        
        return events
