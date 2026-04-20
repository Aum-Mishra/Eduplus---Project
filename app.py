"""
Flask API Server for EduPlus Chatbot - Student Validation
Simplified version focusing on student validation
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import sys
import time
import tempfile
import json
import uuid
import re
import math
import numpy as np
from datetime import datetime, timezone
import requests
from modules.leetcode_dsa import LeetCodeDSA
from modules.github_project import GitHubProject
from modules.hr_round import HRRound
from modules.ml_models import MLModels
from modules.feature_engineering import FeatureEngineering
from modules.salary_probability import SalaryTierPredictor

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENT_CSV = os.path.join(BASE_DIR, 'data', 'student_profiles_100.csv')
PREDICTIONS_CSV = os.path.join(BASE_DIR, 'data', 'Predicted_Data.csv')
BENCHMARK_CSV = os.path.join(BASE_DIR, 'data', 'campus_placement_dataset_final_academic_4000.csv')
CHAT_HISTORY_JSON = os.path.join(BASE_DIR, 'data', 'chat_history.json')
REPORTS_DIR = os.path.join(BASE_DIR, 'data', 'generated_reports')
REQUIRED_PREDICTION_SCORE_COLUMNS = [
    'dsa_score',
    'project_score',
    'aptitude_score',
    'hr_score',
    'resume_ats_score',
]

print(f"[STARTUP] BASE_DIR: {BASE_DIR}")
print(f"[STARTUP] STUDENT_CSV: {STUDENT_CSV}")
print(f"[STARTUP] PREDICTIONS_CSV: {PREDICTIONS_CSV}")
print(f"[STARTUP] STUDENT_CSV exists: {os.path.exists(STUDENT_CSV)}")
print(f"[STARTUP] PREDICTIONS_CSV exists: {os.path.exists(PREDICTIONS_CSV)}")

_BENCHMARK_CACHE = {
    'df': None,
    'mtime': None,
}


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _normalize_student_id(student_id):
    return str(student_id).strip()


def _json_safe(value):
    """Convert values to JSON-safe equivalents (e.g., NaN/Inf -> None)."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]

    # Handle numpy scalar values.
    if hasattr(value, 'item') and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except Exception:
            pass

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def _to_nullable_score(value):
    """Convert value to float score when possible, otherwise None."""
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _build_prediction_input_summary(student_row):
    """Return whether required prediction scores exist for a student row."""
    scores = {}
    missing = []

    for col in REQUIRED_PREDICTION_SCORE_COLUMNS:
        raw_val = student_row.get(col, None)
        parsed = _to_nullable_score(raw_val)
        scores[col] = parsed

        # Scores are considered available only when numeric and in valid range.
        if parsed is None or parsed < 0 or parsed > 100:
            missing.append(col)

    return {
        'available': len(missing) == 0,
        'missing_fields': missing,
        'scores': scores,
    }


def _update_student_profile_scores(student_id, score_updates):
    """Update student score columns in student_profiles_100.csv."""
    if not os.path.exists(STUDENT_CSV):
        raise FileNotFoundError(f"Student CSV not found at {STUDENT_CSV}")

    df = pd.read_csv(STUDENT_CSV)
    if 'student_id' not in df.columns:
        raise ValueError("student_profiles_100.csv is missing 'student_id' column")

    for col in REQUIRED_PREDICTION_SCORE_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"student_profiles_100.csv is missing '{col}' column")

    normalized_id = _normalize_student_id(student_id)
    df['student_id'] = df['student_id'].astype(str).str.strip()
    idx = df[df['student_id'] == normalized_id].index
    if len(idx) == 0:
        raise ValueError(f"Student ID {normalized_id} not found in student_profiles_100.csv")

    row_idx = idx[0]
    for col in REQUIRED_PREDICTION_SCORE_COLUMNS:
        if col not in score_updates:
            continue
        score_val = _to_nullable_score(score_updates.get(col))
        if score_val is None:
            continue
        df.at[row_idx, col] = round(score_val, 2)

    max_retries = 5
    last_err = None
    for attempt in range(max_retries):
        try:
            student_dir = os.path.dirname(STUDENT_CSV)
            fd, tmp_path = tempfile.mkstemp(prefix='student_profiles_', suffix='.tmp', dir=student_dir)
            os.close(fd)

            df.to_csv(tmp_path, index=False)
            os.replace(tmp_path, STUDENT_CSV)
            return True
        except PermissionError as pe:
            last_err = pe
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            time.sleep(0.2 * (2 ** attempt))
        except Exception:
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            raise

    if last_err:
        raise PermissionError(
            f"Could not write to {STUDENT_CSV}. The file appears to be locked by another process."
        )

    return False


def _default_welcome_message():
    return {
        'sender': 'bot',
        'text': "Hello! I'm your AI Placement Assistant. I can help you understand your profile data, placement chances, salary predictions, recommended companies, and skill assessments. What would you like to know?",
        'timestamp': _now_iso(),
        'intent': None,
        'source': 'system',
        'value': None
    }


def _build_chat_title(first_text):
    text = str(first_text or '').strip()
    if not text:
        return 'New Chat'
    text = text.replace('\n', ' ')
    return (text[:57] + '...') if len(text) > 60 else text


def _read_chat_store():
    if not os.path.exists(CHAT_HISTORY_JSON):
        return {}
    try:
        with open(CHAT_HISTORY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe_write_chat_store(store):
    os.makedirs(os.path.dirname(CHAT_HISTORY_JSON), exist_ok=True)
    last_err = None
    for attempt in range(3):
        fd, tmp_path = tempfile.mkstemp(prefix='chat_history_', suffix='.tmp', dir=os.path.dirname(CHAT_HISTORY_JSON))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_file:
                json.dump(store, tmp_file, ensure_ascii=False, indent=2)
            os.replace(tmp_path, CHAT_HISTORY_JSON)
            return True
        except PermissionError as e:
            last_err = e
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            time.sleep(0.1 * (attempt + 1))
        except Exception:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise
    if last_err:
        raise last_err


def _ensure_student_history(store, student_id):
    sid = _normalize_student_id(student_id)
    if sid not in store or not isinstance(store.get(sid), dict):
        store[sid] = {'active_chat_id': None, 'chats': []}
    if 'chats' not in store[sid] or not isinstance(store[sid].get('chats'), list):
        store[sid]['chats'] = []
    if 'active_chat_id' not in store[sid]:
        store[sid]['active_chat_id'] = None
    return store[sid]


def _find_chat(student_history, chat_id):
    for chat in student_history.get('chats', []):
        if str(chat.get('chat_id')) == str(chat_id):
            return chat
    return None


def _create_chat_session(store, student_id, title=None):
    now = _now_iso()
    student_history = _ensure_student_history(store, student_id)
    chat_id = f"chat_{uuid.uuid4().hex[:12]}"
    chat = {
        'chat_id': chat_id,
        'title': str(title or 'New Chat'),
        'created_at': now,
        'updated_at': now,
        'messages': [_default_welcome_message()]
    }
    student_history['chats'].append(chat)
    student_history['active_chat_id'] = chat_id
    return chat


def _sort_chats_desc(chats):
    return sorted(chats, key=lambda c: c.get('updated_at', ''), reverse=True)


def _append_chat_message(store, student_id, chat_id, sender, text, intent=None, source=None, value=None):
    now = _now_iso()
    sid = _normalize_student_id(student_id)
    student_history = _ensure_student_history(store, sid)

    active_chat_id = str(chat_id).strip() if chat_id else student_history.get('active_chat_id')
    chat = _find_chat(student_history, active_chat_id) if active_chat_id else None
    if chat is None:
        chat = _create_chat_session(store, sid)
        active_chat_id = chat.get('chat_id')

    msg = {
        'sender': sender,
        'text': str(text),
        'timestamp': now,
        'intent': intent,
        'source': source,
        'value': value
    }
    chat.setdefault('messages', []).append(msg)
    chat['updated_at'] = now

    if sender == 'user' and chat.get('title', 'New Chat') == 'New Chat':
        chat['title'] = _build_chat_title(text)

    student_history['active_chat_id'] = active_chat_id
    return active_chat_id


def _serialize_student_history(student_id, student_history):
    chats = _sort_chats_desc(student_history.get('chats', []))
    return {
        'student_id': _normalize_student_id(student_id),
        'active_chat_id': student_history.get('active_chat_id'),
        'chats': chats
    }

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'EduPlus API is running'}), 200


@app.route('/api/auth/login', methods=['POST'])
def login_student():
    """Unified login endpoint for student portal.

    Current rule for this deployment: password must match student ID.
    """
    try:
        payload = request.json or {}
        raw_student_id = str(payload.get('student_id', '')).strip()
        raw_password = str(payload.get('password', '')).strip()

        if not raw_student_id or not raw_password:
            return jsonify({'success': False, 'message': 'Student ID and password are required'}), 400

        if raw_password != raw_student_id:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

        if not os.path.exists(STUDENT_CSV):
            return jsonify({'success': False, 'message': 'Student database is not available'}), 500

        df = pd.read_csv(STUDENT_CSV)
        if 'student_id' not in df.columns:
            return jsonify({'success': False, 'message': 'Student database schema is invalid'}), 500

        df['student_id'] = df['student_id'].astype(str).str.strip()
        student = df[df['student_id'] == raw_student_id]
        if student.empty:
            return jsonify({'success': False, 'message': 'Student ID not found'}), 404

        student_row = student.iloc[0].to_dict()
        student_name = str(student_row.get('name', f'Student {raw_student_id}'))

        return jsonify({
            'success': True,
            'student_id': int(raw_student_id) if raw_student_id.isdigit() else raw_student_id,
            'name': student_name,
            'student': _json_safe(student_row),
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== STUDENT VALIDATION ====================

@app.route('/api/student/<student_id>', methods=['GET'])
def get_student(student_id):
    """Get student info and validate if student exists"""
    print(f"\n[REQUEST] GET /api/student/{student_id}")
    try:
        # Validate CSV file exists
        if not os.path.exists(STUDENT_CSV):
            error_msg = f"Student CSV not found at {STUDENT_CSV}"
            print(f"[ERROR] {error_msg}")
            return jsonify({'exists': False, 'message': error_msg}), 404
        
        # Load student data
        print(f"[DEBUG] Loading student data from {STUDENT_CSV}")
        df = pd.read_csv(STUDENT_CSV)
        print(f"[DEBUG] Loaded {len(df)} students from CSV")
        print(f"[DEBUG] Column names: {list(df.columns)}")
        print(f"[DEBUG] Looking for student_id: '{student_id}' (type: {type(student_id).__name__})")
        
        # Normalize student_id for comparison
        df['student_id'] = df['student_id'].astype(str).str.strip()
        search_id = str(student_id).strip()
        
        print(f"[DEBUG] Search ID (normalized): '{search_id}'")
        print(f"[DEBUG] Sample student IDs from CSV: {df['student_id'].head(5).tolist()}")
        
        # Find matching student
        student = df[df['student_id'] == search_id]
        print(f"[DEBUG] Found {len(student)} matching students")
        
        if len(student) == 0:
            print(f"[ERROR] Student {search_id} not found in CSV")
            return jsonify({
                'exists': False,
                'message': 'Student ID not found in database',
                'student_id': student_id
            }), 404
        
        # Extract student info
        student_row = student.iloc[0]
        student_name = str(student_row.get('name', 'Unknown'))
        
        print(f"[SUCCESS] Found student: {student_name} (ID: {search_id})")
        
        # Check for prediction data
        last_prediction = None
        if os.path.exists(PREDICTIONS_CSV):
            try:
                pred_df = pd.read_csv(PREDICTIONS_CSV)
                pred_df['student_id'] = pred_df['student_id'].astype(str).str.strip()
                pred = pred_df[pred_df['student_id'] == search_id]
                
                if not pred.empty:
                    last_prediction = pred.iloc[0].to_dict()
                    print(f"[DEBUG] Found prediction for student {search_id}")
                else:
                    print(f"[DEBUG] No prediction found for student {search_id}")
            except Exception as pe:
                print(f"[WARN] Error reading predictions: {pe}")
        else:
            print(f"[WARN] Predictions file not found at {PREDICTIONS_CSV}")
        
        # Prepare response
        response = {
            'exists': True,
            'name': student_name,
            'id': student_id,
            'student_id': student_id,
            'data': _json_safe(student_row.to_dict()),
            'prediction_input': _build_prediction_input_summary(student_row),
            'lastPrediction': _json_safe(last_prediction)
        }
        
        print(f"[RESPONSE] Status: 200 OK")
        return jsonify(response), 200
    
    except pd.errors.ParserError as pe:
        error_msg = f"CSV parsing error: {str(pe)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({'error': error_msg, 'exists': False}), 500
    
    except Exception as e:
        error_msg = str(e)
        print(f"[EXCEPTION] {type(e).__name__}: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg, 'exists': False}), 500

# ==================== CHATBOT MESSAGE ====================

RASA_WEBHOOK_URL = 'http://localhost:5005/webhooks/rest/webhook'

# ==================== INTEGRATIONS ====================

@app.route('/api/integrations/leetcode', methods=['POST'])
def fetch_leetcode():
    """Fetch LeetCode score from username."""
    try:
        data = request.json or {}
        username = str(data.get('username', '')).strip()

        if not username:
            return jsonify({'error': 'Username required', 'score': None}), 400

        print(f"[LeetCode] Fetching score for username: {username}")
        leetcode = LeetCodeDSA(username)
        lc_data = leetcode.fetch_leetcode_data()

        if lc_data is None:
            print(f"[LeetCode] Username '{username}' not found or API error")
            return jsonify({
                'error': 'Username not found. Please enter score manually.',
                'score': None,
                'username': username
            }), 200

        score = leetcode.calculate_dsa_score()
        print(f"[LeetCode] Successfully calculated score: {score} for user: {username}")

        return jsonify({
            'score': score,
            'username': username,
            'source': 'leetcode',
            'data': lc_data
        }), 200

    except Exception as e:
        print(f"[LeetCode] Exception: {str(e)}")
        return jsonify({'error': f'Error fetching LeetCode data: {str(e)}', 'score': None}), 200


@app.route('/api/integrations/github', methods=['POST'])
def fetch_github():
    """Fetch GitHub score from username."""
    try:
        data = request.json or {}
        username = str(data.get('username', '')).strip()

        if not username:
            return jsonify({'error': 'Username required', 'score': None}), 400

        import requests
        response = requests.get(
            f'https://api.github.com/users/{username}',
            timeout=6,
            headers={'Accept': 'application/vnd.github.v3+json'}
        )

        if response.status_code != 200:
            return jsonify({
                'error': 'GitHub username not found. Please enter score manually.',
                'score': None,
                'username': username
            }), 200

        user_data = response.json()
        public_repos = int(user_data.get('public_repos', 0))
        followers = int(user_data.get('followers', 0))

        score = min(30 + (public_repos * 3) + (followers * 0.5), 100)
        score = round(max(score, 0), 2)

        return jsonify({
            'score': score,
            'username': username,
            'source': 'github',
            'public_repos': public_repos,
            'followers': followers
        }), 200

    except Exception as e:
        print(f"[GitHub] Exception: {str(e)}")
        return jsonify({'error': f'Error fetching GitHub data: {str(e)}', 'score': None}), 200


@app.route('/api/integrations/github-projects', methods=['POST'])
def evaluate_github_projects():
    """Evaluate GitHub repositories and return project score."""
    try:
        data = request.json or {}
        repo_urls = data.get('repo_urls', [])

        if not repo_urls:
            return jsonify({'error': 'No repositories provided', 'score': None}), 400

        github = GitHubProject()
        average_score = github.evaluate_multiple_projects(repo_urls)

        sanitized_repos = []
        for repo in github.repos:
            safe_repo = {}
            for key, value in repo.items():
                if isinstance(value, (int, float, bool)):
                    safe_repo[key] = value
                elif isinstance(value, list):
                    safe_repo[key] = [str(v) for v in value]
                else:
                    safe_repo[key] = str(value)
            sanitized_repos.append(safe_repo)

        return jsonify({
            'score': float(average_score),
            'repo_count': len(repo_urls),
            'repos': sanitized_repos,
            'message': f'Analyzed {len(repo_urls)} repositories'
        }), 200

    except Exception as e:
        print(f"[GitHub Projects] Exception: {str(e)}")
        return jsonify({'error': f'Error evaluating repositories: {str(e)}', 'score': None}), 200


@app.route('/api/aptitude/links', methods=['GET'])
def get_aptitude_links():
    """Get aptitude and ATS test links."""
    aptitude_url = 'https://aptitude-test.com/'
    ats_url = 'https://enhancv.com/resources/resume-checker/'
    return jsonify({
        'aptitude_url': aptitude_url,
        'ats_url': ats_url,
        'aptitude': {
            'link': aptitude_url
        },
        'ats': {
            'link': ats_url
        }
    }), 200


@app.route('/api/hr-round/questions', methods=['GET'])
def get_hr_questions():
    """Get HR round questions."""
    questions = [
        "Describe a project where you had a major responsibility. What was your role?",
        "Tell me about a time when your team faced a problem. How did you handle it?",
        "Describe a failure or mistake you made in a project. What did you learn?",
        "How do you handle pressure or tight deadlines?",
        "Explain a situation where you had to learn something new quickly."
    ]
    return jsonify({'questions': questions}), 200


@app.route('/api/hr-round/evaluate', methods=['POST'])
def evaluate_hr_round():
    """Evaluate HR round answers."""
    try:
        data = request.json or {}
        answers = data.get('answers', [])

        if not answers:
            return jsonify({'error': 'No answers provided', 'score': None}), 400

        hr = HRRound()
        hr.answers = answers
        hr_score = hr.calculate_hr_score()

        return jsonify({
            'score': float(hr_score),
            'breakdown': {
                'communication': float(hr.scores.get('communication', 0)),
                'star_structure': float(hr.scores.get('star_structure', 0)),
                'ownership': float(hr.scores.get('ownership', 0)),
                'consistency': float(hr.scores.get('consistency', 0))
            },
            'message': 'HR evaluation complete'
        }), 200

    except Exception as e:
        print(f"[HR Round] Exception: {str(e)}")
        return jsonify({'error': f'Error evaluating HR round: {str(e)}', 'score': None}), 200


# ==================== PREDICTIONS ====================

def _as_float(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _load_benchmark_df():
    """Load benchmark dataset with a small file-mtime cache."""
    try:
        if not os.path.exists(BENCHMARK_CSV):
            return pd.DataFrame()

        mtime = os.path.getmtime(BENCHMARK_CSV)
        if _BENCHMARK_CACHE['df'] is not None and _BENCHMARK_CACHE['mtime'] == mtime:
            return _BENCHMARK_CACHE['df'].copy()

        df = pd.read_csv(BENCHMARK_CSV)
        _BENCHMARK_CACHE['df'] = df
        _BENCHMARK_CACHE['mtime'] = mtime
        return df.copy()
    except Exception:
        return pd.DataFrame()


def _empirical_percentile(series, value):
    vals = pd.to_numeric(series, errors='coerce').dropna()
    if vals.empty:
        return None
    return round(float((vals <= float(value)).mean() * 100.0), 2)


def _build_feature_vector_row(raw):
    dsa = _as_float(raw.get('dsa_score'), 50)
    project = _as_float(raw.get('project_score'), 50)
    cs = _as_float(raw.get('cs_fundamentals_score'), 50)
    aptitude = _as_float(raw.get('aptitude_score'), 50)
    hr = _as_float(raw.get('hr_score'), 50)

    return {
        'cgpa': _as_float(raw.get('cgpa'), 7.0),
        'project_score': project,
        'dsa_score': dsa,
        'hackathon_wins': _as_float(raw.get('hackathon_wins'), 0),
        'aptitude_score': aptitude,
        'hr_score': hr,
        'resume_ats_score': _as_float(raw.get('resume_ats_score'), 50),
        'cs_fundamentals_score': cs,
        'technical_score': (dsa + project + cs) / 3.0,
        'soft_skill_score': (aptitude + hr) / 2.0,
    }


def _estimate_prediction_snapshot(student_data, models_obj):
    """Compute placement probability and salary estimate using the current model stack."""
    fe = FeatureEngineering()
    fe.fitted = True
    fe.scaler = models_obj.scaler
    student_features = fe.prepare_student_input(student_data)

    # Placement probability
    try:
        raw_prob = float(models_obj.placement_model.predict_proba([student_features])[0][1])
    except Exception:
        raw_prob = 0.5

    raw_prob_pct = raw_prob * 100.0
    p = raw_prob

    if raw_prob_pct > 30.0:
        skill_avg = (
            _as_float(student_data.get('dsa_score'), 50) +
            _as_float(student_data.get('project_score'), 50) +
            _as_float(student_data.get('cs_fundamentals_score'), 50)
        ) / 3.0
        soft_avg = (_as_float(student_data.get('aptitude_score'), 50) + _as_float(student_data.get('hr_score'), 50)) / 2.0
        ats_score = _as_float(student_data.get('resume_ats_score'), 50)
        cgpa = _as_float(student_data.get('cgpa'), 7.0)

        if skill_avg < 40.0:
            p *= 0.4
        if ats_score < 35.0:
            p *= 0.5
        if soft_avg < 40.0:
            p *= 0.6
        if cgpa < 6.0:
            p *= 0.5

    placement_pct = round(max(0.05, min(1.0, p)) * 100.0, 2)

    # Salary estimate
    try:
        if models_obj.salary_model:
            salary_pred_raw = float(models_obj.salary_model.predict([student_features])[0])
            salary_lpa = round(max(3.0, min(50.0, salary_pred_raw)), 2)
        else:
            salary_lpa = 5.0
    except Exception:
        salary_lpa = 5.0

    return {
        'placement_probability_pct': placement_pct,
        'predicted_salary_lpa': salary_lpa,
    }


def _build_peer_comparison(student_data, benchmark_df):
    if benchmark_df.empty:
        return {
            'available': False,
            'message': 'Benchmark dataset not available for peer comparison.',
        }

    work = benchmark_df.copy()
    for col, fallback in [
        ('dsa_score', 50), ('project_score', 50), ('cs_fundamentals_score', 50),
        ('aptitude_score', 50), ('hr_score', 50), ('resume_ats_score', 50), ('cgpa', 7.0)
    ]:
        if col not in work.columns:
            work[col] = fallback

    work['technical_score'] = (
        pd.to_numeric(work['dsa_score'], errors='coerce').fillna(50) +
        pd.to_numeric(work['project_score'], errors='coerce').fillna(50) +
        pd.to_numeric(work['cs_fundamentals_score'], errors='coerce').fillna(50)
    ) / 3.0

    dsa = _as_float(student_data.get('dsa_score'), 50)
    project = _as_float(student_data.get('project_score'), 50)
    cs = _as_float(student_data.get('cs_fundamentals_score'), 50)
    technical = (dsa + project + cs) / 3.0

    p_technical = _empirical_percentile(work['technical_score'], technical)
    p_dsa = _empirical_percentile(work['dsa_score'], dsa)
    p_project = _empirical_percentile(work['project_score'], project)

    dsa_q75 = round(float(pd.to_numeric(work['dsa_score'], errors='coerce').dropna().quantile(0.75)), 2)
    project_q75 = round(float(pd.to_numeric(work['project_score'], errors='coerce').dropna().quantile(0.75)), 2)
    technical_q75 = round(float(pd.to_numeric(work['technical_score'], errors='coerce').dropna().quantile(0.75)), 2)

    bottom_pct = p_technical if p_technical is not None else None

    return {
        'available': True,
        'student_percentiles': {
            'technical_percentile': p_technical,
            'dsa_percentile': p_dsa,
            'project_percentile': p_project,
        },
        'bottom_bucket_statement': (
            f"You are currently in the bottom {round(bottom_pct, 1)}% for technical score among benchmark students."
            if bottom_pct is not None else
            'Technical percentile could not be computed.'
        ),
        'top_25_percent_thresholds': {
            'dsa_score_q75': dsa_q75,
            'project_score_q75': project_q75,
            'technical_score_q75': technical_q75,
        },
    }


def _build_confidence_reliability(student_data, models_obj, benchmark_df):
    if benchmark_df.empty or not getattr(models_obj, 'scaler', None):
        return {
            'available': False,
            'confidence_label': 'Unknown',
            'uncertainty_pct': None,
            'reason': 'Insufficient benchmark data to estimate reliability.',
        }

    work = benchmark_df.copy()
    for col, fallback in [
        ('cgpa', 7.0), ('project_score', 50), ('dsa_score', 50), ('hackathon_wins', 0),
        ('aptitude_score', 50), ('hr_score', 50), ('resume_ats_score', 50), ('cs_fundamentals_score', 50),
        ('salary_lpa', np.nan), ('expected_salary', np.nan)
    ]:
        if col not in work.columns:
            work[col] = fallback

    work['salary_reference'] = pd.to_numeric(work.get('salary_lpa'), errors='coerce')
    if work['salary_reference'].isna().all():
        work['salary_reference'] = pd.to_numeric(work.get('expected_salary'), errors='coerce')

    high_salary = work[work['salary_reference'] >= 10].copy()
    if high_salary.empty:
        high_salary = work.copy()

    # Build feature matrices.
    feature_rows = high_salary.apply(_build_feature_vector_row, axis=1, result_type='expand')
    try:
        X_ref = models_obj.scaler.transform(feature_rows)
    except Exception:
        return {
            'available': False,
            'confidence_label': 'Unknown',
            'uncertainty_pct': None,
            'reason': 'Scaler transformation failed while estimating reliability.',
        }

    student_row = _build_feature_vector_row(student_data)
    X_student = models_obj.scaler.transform(pd.DataFrame([student_row]))[0]

    distances = np.linalg.norm(X_ref - X_student, axis=1)
    if len(distances) == 0:
        return {
            'available': False,
            'confidence_label': 'Unknown',
            'uncertainty_pct': None,
            'reason': 'Not enough comparable profiles for reliability estimate.',
        }

    k = min(25, len(distances))
    nearest_mean = float(np.mean(np.partition(distances, k - 1)[:k]))
    distance_scale = float(np.percentile(distances, 90)) if len(distances) > 5 else float(np.max(distances))
    distance_scale = max(distance_scale, 1e-6)
    d_norm = max(0.0, min(1.5, nearest_mean / distance_scale))

    sigma_model = 8.0
    alpha = 0.8
    uncertainty = round(max(6.0, min(20.0, sigma_model * (1.0 + alpha * d_norm))), 1)

    if uncertainty <= 9.5:
        label = 'High'
    elif uncertainty <= 14.0:
        label = 'Medium'
    else:
        label = 'Low'

    return {
        'available': True,
        'confidence_label': label,
        'uncertainty_pct': uncertainty,
        'nearest_profile_distance': round(nearest_mean, 3),
        'distance_normalized': round(d_norm, 3),
        'reason': (
            'Low data similarity with high-salary benchmark profiles.'
            if d_norm >= 0.9 else
            'Moderate similarity with benchmark profiles used during model learning.'
            if d_norm >= 0.6 else
            'Strong similarity with benchmark profiles used during model learning.'
        ),
    }


def _build_risk_alerts(student_data):
    alerts = []

    dsa = _as_float(student_data.get('dsa_score'), 50)
    project = _as_float(student_data.get('project_score'), 50)
    ats = _as_float(student_data.get('resume_ats_score'), 50)
    cgpa = _as_float(student_data.get('cgpa'), 7.0)
    github_projects = int(_as_float(student_data.get('github_projects'), 0))

    if dsa < 10:
        alerts.append({
            'severity': 'Critical',
            'title': 'DSA score below 10',
            'risk': 'High rejection probability in OA and coding rounds.',
        })
    elif dsa < 30:
        alerts.append({
            'severity': 'High',
            'title': 'Very low DSA score',
            'risk': 'Low coding-round conversion probability in technical hiring pipelines.',
        })

    if github_projects <= 0 or project <= 10:
        alerts.append({
            'severity': 'Critical',
            'title': 'No project depth',
            'risk': 'Resume shortlisting risk due to limited project evidence.',
        })
    elif project < 40:
        alerts.append({
            'severity': 'High',
            'title': 'Low project score',
            'risk': 'Weak project quality can hurt resume and interview discussion outcomes.',
        })

    if ats < 35:
        alerts.append({
            'severity': 'High',
            'title': 'Low ATS score',
            'risk': 'Profile may be filtered out before interview rounds.',
        })

    if cgpa < 6.0:
        alerts.append({
            'severity': 'High',
            'title': 'CGPA below common cutoffs',
            'risk': 'Eligibility risk for multiple companies with strict academic criteria.',
        })

    return alerts


def _build_projected_improvement(student_data, models_obj):
    current_snapshot = _estimate_prediction_snapshot(student_data, models_obj)

    scenario = dict(student_data)
    scenario['dsa_score'] = max(_as_float(student_data.get('dsa_score'), 50), 50.0)
    scenario['project_score'] = max(_as_float(student_data.get('project_score'), 50), 60.0)
    scenario['cs_fundamentals_score'] = max(_as_float(student_data.get('cs_fundamentals_score'), 50), 55.0)
    scenario['resume_ats_score'] = max(_as_float(student_data.get('resume_ats_score'), 50), 60.0)
    scenario['aptitude_score'] = max(_as_float(student_data.get('aptitude_score'), 50), 55.0)
    scenario['hr_score'] = max(_as_float(student_data.get('hr_score'), 50), 55.0)

    projected_snapshot = _estimate_prediction_snapshot(scenario, models_obj)

    return {
        'available': True,
        'simulation_note': 'Projected values are scenario-based estimates using the same model pipeline, not guaranteed outcomes.',
        'changes_assumed': {
            'dsa_score': {
                'current': round(_as_float(student_data.get('dsa_score'), 0), 2),
                'projected': round(_as_float(scenario.get('dsa_score'), 0), 2),
            },
            'project_score': {
                'current': round(_as_float(student_data.get('project_score'), 0), 2),
                'projected': round(_as_float(scenario.get('project_score'), 0), 2),
            },
        },
        'placement_probability': {
            'current': current_snapshot['placement_probability_pct'],
            'projected': projected_snapshot['placement_probability_pct'],
            'delta': round(projected_snapshot['placement_probability_pct'] - current_snapshot['placement_probability_pct'], 2),
        },
        'predicted_salary_lpa': {
            'current': current_snapshot['predicted_salary_lpa'],
            'projected': projected_snapshot['predicted_salary_lpa'],
            'delta': round(projected_snapshot['predicted_salary_lpa'] - current_snapshot['predicted_salary_lpa'], 2),
        },
    }


def _has_advanced_low_report_sections(report_obj):
    if not isinstance(report_obj, dict):
        return False
    required = ['peer_comparison', 'confidence_reliability', 'risk_alerts', 'projected_improvement']
    return all(k in report_obj for k in required)

def _build_low_probability_report(student_data, placement_probability_pct, models_obj):
    """Build data-grounded reasons and practical actions for low placement probability."""
    prob = float(placement_probability_pct)
    is_low = prob < 30.0

    dsa = float(student_data.get('dsa_score', 0.0))
    project = float(student_data.get('project_score', 0.0))
    cs = float(student_data.get('cs_fundamentals_score', 0.0))
    aptitude = float(student_data.get('aptitude_score', 0.0))
    hr = float(student_data.get('hr_score', 0.0))
    ats = float(student_data.get('resume_ats_score', 0.0))
    cgpa = float(student_data.get('cgpa', 0.0))

    technical_avg = round((dsa + project + cs) / 3.0, 2)
    soft_avg = round((aptitude + hr) / 2.0, 2)

    reasons = []
    actions = []

    def add_reason(parameter, current, target, impact, why_it_matters):
        reasons.append({
            'parameter': parameter,
            'current': round(float(current), 2),
            'target': round(float(target), 2),
            'gap': round(float(target) - float(current), 2),
            'impact': impact,
            'why_it_matters': why_it_matters,
        })

    def add_action(focus_area, action, target, timeline):
        actions.append({
            'focus_area': focus_area,
            'action': action,
            'target': target,
            'timeline': timeline,
        })

    if technical_avg < 40.0:
        add_reason(
            'Technical Foundation (DSA + Projects + CS Fundamentals)',
            technical_avg,
            60.0,
            'High',
            'Low technical depth significantly reduces shortlisting and coding-round conversion.'
        )
        add_action(
            'Technical Foundation',
            'Practice 120 structured DSA problems and complete CS fundamentals revision with weekly coding mocks.',
            'Raise technical average to 60+',
            '6-8 weeks'
        )

    if ats < 35.0:
        add_reason(
            'Resume ATS Score',
            ats,
            60.0,
            'High',
            'Low ATS score blocks resume shortlisting before interviews start.'
        )
        add_action(
            'Resume and ATS',
            'Rewrite resume with role keywords, quantified project outcomes, and clean one-page structure; run ATS check each week.',
            'Increase ATS score to 60+',
            '2-3 weeks'
        )

    if soft_avg < 40.0:
        add_reason(
            'Aptitude and HR Readiness',
            soft_avg,
            55.0,
            'Medium',
            'Weak aptitude/HR readiness lowers performance in screening and interview rounds.'
        )
        add_action(
            'Aptitude and HR',
            'Take timed aptitude practice and 10 mock HR answers using STAR format with mentor feedback.',
            'Raise soft-skill average to 55+',
            '4-6 weeks'
        )

    if cgpa < 6.0:
        add_reason(
            'CGPA Eligibility',
            cgpa,
            6.5,
            'High',
            'Lower CGPA can make you ineligible for many companies and reduces opportunities.'
        )
        add_action(
            'Academic Eligibility',
            'Prioritize upcoming semester GPA and clear any backlogs to meet more company cutoffs.',
            'Reach CGPA 6.5+',
            '1-2 semesters'
        )

    if dsa < 55.0:
        add_reason(
            'DSA Score',
            dsa,
            70.0,
            'High',
            'DSA heavily influences online assessments and technical interview rounds.'
        )
        add_action(
            'DSA',
            'Follow a company-focused roadmap: arrays/strings, trees, graphs, DP; attempt 5 timed problems daily.',
            'Raise DSA score to 70+',
            '8-10 weeks'
        )

    if project < 60.0:
        add_reason(
            'Project Quality',
            project,
            70.0,
            'Medium',
            'Low-impact projects weaken profile credibility during resume and interview discussion.'
        )
        add_action(
            'Projects',
            'Upgrade 2 projects with deployment, measurable outcomes, and clear architecture explanation.',
            'Raise project score to 70+',
            '4-6 weeks'
        )

    if not reasons:
        add_reason(
            'Overall Profile Consistency',
            prob,
            45.0,
            'Medium',
            'Current scores are moderate but not strong enough yet for consistent placement conversion.'
        )
        add_action(
            'Consistency Sprint',
            'Improve weakest two scores by at least 10 points with weekly tracking and mock test reviews.',
            'Move placement probability above 45%',
            '6 weeks'
        )

    reasons = sorted(reasons, key=lambda x: {'High': 0, 'Medium': 1, 'Low': 2}.get(x['impact'], 3))

    benchmark_df = _load_benchmark_df()
    peer_comparison = _build_peer_comparison(student_data, benchmark_df)
    confidence_reliability = _build_confidence_reliability(student_data, models_obj, benchmark_df)
    risk_alerts = _build_risk_alerts(student_data)
    projected_improvement = _build_projected_improvement(student_data, models_obj)

    return {
        'is_low_probability_case': is_low,
        'threshold_pct': 30.0,
        'current_probability_pct': round(prob, 2),
        'data_snapshot': {
            'dsa_score': round(dsa, 2),
            'project_score': round(project, 2),
            'cs_fundamentals_score': round(cs, 2),
            'aptitude_score': round(aptitude, 2),
            'hr_score': round(hr, 2),
            'resume_ats_score': round(ats, 2),
            'cgpa': round(cgpa, 2),
            'technical_average': technical_avg,
            'soft_skill_average': soft_avg,
        },
        'summary': (
            'Your placement probability is currently below 30% because one or more core profile factors '
            'are below practical hiring expectations. Improve the high-impact gaps first.'
        ) if is_low else 'Your probability is not in the low band.',
        'reasons': reasons,
        'practical_changes': actions,
        'peer_comparison': peer_comparison,
        'confidence_reliability': confidence_reliability,
        'risk_alerts': risk_alerts,
        'projected_improvement': projected_improvement,
        'final_note': 'If you implement these changes consistently, your prediction can improve in the next update cycle.',
    }

@app.route('/api/predictions/generate', methods=['POST'])
def generate_predictions():
    """Generate placement predictions from input scores."""
    try:
        data = request.json or {}

        student_data = {
            'student_id': data.get('studentId'),
            'dsa_score': float(data.get('dsa_score', 50)),
            'project_score': float(data.get('project_score', 50)),
            'aptitude_score': float(data.get('aptitude_score', 50)),
            'hr_score': float(data.get('hr_score', 50)),
            'resume_ats_score': float(data.get('resume_ats_score', 50)),
            'github_projects': int(data.get('github_projects', 0)),
            'github_project_links': data.get('github_project_links', []),
            # Optional fields used by ML/penalty logic
            'cs_fundamentals_score': float(data.get('cs_fundamentals_score', 50.0)),
            'cgpa': float(data.get('cgpa', 7.0)),
            'hackathon_wins': int(data.get('hackathon_wins', 0)),
        }

        # Persist generated/entered scores back to student profiles before prediction output.
        _update_student_profile_scores(
            student_data['student_id'],
            {
                'dsa_score': student_data['dsa_score'],
                'project_score': student_data['project_score'],
                'aptitude_score': student_data['aptitude_score'],
                'hr_score': student_data['hr_score'],
                'resume_ats_score': student_data['resume_ats_score'],
            }
        )

        print(f"[PREDICTION] Generating prediction for student {student_data['student_id']}")

        models_obj = MLModels()
        if not models_obj.load_models():
            raise Exception("Failed to load ML models")

        fe = FeatureEngineering()
        fe.fitted = True
        fe.scaler = models_obj.scaler
        student_features = fe.prepare_student_input(student_data)

        # Raw probability from ML model (0..1)
        try:
            raw_prob = float(models_obj.placement_model.predict_proba([student_features])[0][1])
        except Exception as e:
            print(f"[PREDICTION] Error getting placement probability: {e}")
            raw_prob = 0.5

        raw_prob_pct = raw_prob * 100.0
        p = raw_prob

        # Penalties apply only if raw placement probability is above 30%
        if raw_prob_pct > 30.0:
            skill_avg = (
                student_data['dsa_score'] +
                student_data['project_score'] +
                student_data['cs_fundamentals_score']
            ) / 3.0
            soft_avg = (student_data['aptitude_score'] + student_data['hr_score']) / 2.0
            ats_score = student_data['resume_ats_score']
            cgpa = student_data['cgpa']

            if skill_avg < 40.0:
                p *= 0.4
                print(f"[PREDICTION] Applied skill penalty x0.4 (avg={skill_avg:.2f})")
            if ats_score < 35.0:
                p *= 0.5
                print(f"[PREDICTION] Applied ATS penalty x0.5 (ats={ats_score:.2f})")
            if soft_avg < 40.0:
                p *= 0.6
                print(f"[PREDICTION] Applied soft-skill penalty x0.6 (avg={soft_avg:.2f})")
            if cgpa < 6.0:
                p *= 0.5
                print(f"[PREDICTION] Applied CGPA penalty x0.5 (cgpa={cgpa:.2f})")
        else:
            print(f"[PREDICTION] Raw probability {raw_prob_pct:.2f}% <= 30%, penalties skipped")

        ml_placement_prob = max(0.05, min(1.0, p))
        placement_probability_pct = float(round(ml_placement_prob * 100, 2))
        low_probability_report = _build_low_probability_report(student_data, placement_probability_pct, models_obj)

        # Salary prediction
        try:
            if models_obj.salary_model:
                salary_pred_raw = float(models_obj.salary_model.predict([student_features])[0])
                salary_pred = max(3.0, min(50.0, salary_pred_raw))
            else:
                salary_pred = 5.0
        except Exception as e:
            print(f"[PREDICTION] Error predicting salary: {e}")
            salary_pred = 5.0

        # Salary distribution and threshold probabilities
        try:
            salary_predictor = SalaryTierPredictor()
            if salary_predictor.load_model():
                salary_distribution = salary_predictor.predict_salary_distribution(student_data)
            else:
                salary_distribution = {
                    "0-5 LPA": 40.0,
                    "5-10 LPA": 30.0,
                    "10-15 LPA": 15.0,
                    "15-20 LPA": 8.0,
                    "20-30 LPA": 5.0,
                    "30-40 LPA": 1.5,
                    ">40 LPA": 0.5,
                }
        except Exception as e:
            print(f"[PREDICTION] Error getting salary distribution: {e}")
            salary_distribution = {
                "0-5 LPA": 40.0,
                "5-10 LPA": 30.0,
                "10-15 LPA": 15.0,
                "15-20 LPA": 8.0,
                "20-30 LPA": 5.0,
                "30-40 LPA": 1.5,
                ">40 LPA": 0.5,
            }

        # Job role prediction
        role_name = "Software Engineer"
        try:
            if models_obj.jobrole_model and models_obj.role_encoder:
                role_pred = models_obj.jobrole_model.predict([student_features])[0]
                role_name = str(models_obj.role_encoder.inverse_transform([role_pred])[0])
        except Exception as e:
            print(f"[PREDICTION] Error predicting job role: {e}")

        # Company recommendations
        recommended_companies = []
        try:
            if models_obj.knn_companies and models_obj.companies_list is not None:
                _, indices = models_obj.knn_companies.kneighbors([student_features], n_neighbors=5)
                recommended_companies = [str(models_obj.companies_list[idx]) for idx in indices[0]]
        except Exception as e:
            print(f"[PREDICTION] Error getting company recommendations: {e}")

        # Normalize distribution to percentage-like values
        p_0_5 = float(salary_distribution.get("0-5 LPA", 0.0))
        p_5_10 = float(salary_distribution.get("5-10 LPA", 0.0))
        p_10_15 = float(salary_distribution.get("10-15 LPA", 0.0))
        p_15_20 = float(salary_distribution.get("15-20 LPA", 0.0))
        p_20_30 = float(salary_distribution.get("20-30 LPA", 0.0))
        p_30_40 = float(salary_distribution.get("30-40 LPA", 0.0))
        p_above_40 = float(salary_distribution.get(">40 LPA", 0.0))

        derived_probs = {
            ">2 LPA": round((3/5 * p_0_5) + p_5_10 + p_10_15 + p_15_20 + p_20_30 + p_30_40 + p_above_40, 1),
            ">5 LPA": round(p_5_10 + p_10_15 + p_15_20 + p_20_30 + p_30_40 + p_above_40, 1),
            ">10 LPA": round(p_10_15 + p_15_20 + p_20_30 + p_30_40 + p_above_40, 1),
            ">15 LPA": round(p_15_20 + p_20_30 + p_30_40 + p_above_40, 1),
            ">20 LPA": round(p_20_30 + p_30_40 + p_above_40, 1),
            ">25 LPA": round((5/10 * p_20_30) + p_30_40 + p_above_40, 1),
            ">30 LPA": round(p_30_40 + p_above_40, 1),
            ">35 LPA": round((5/10 * p_30_40) + p_above_40, 1),
            ">40 LPA": round(p_above_40, 1),
        }

        salary_min = max(0.0, salary_pred * 0.7)
        salary_mid = salary_pred
        salary_max = max(0.0, salary_pred * 1.3)

        response_data = {
            'success': True,
            'overall_placement_probability': placement_probability_pct,
            'predicted_salary_lpa': float(round(salary_pred, 2)),
            'salary_range_min_lpa': float(round(salary_min, 2)),
            'salary_range_mid_lpa': float(round(salary_mid, 2)),
            'salary_range_max_lpa': float(round(salary_max, 2)),
            'prob_salary_gt_2_lpa': float(derived_probs.get(">2 LPA", 0.0)),
            'prob_salary_gt_5_lpa': float(derived_probs.get(">5 LPA", 0.0)),
            'prob_salary_gt_10_lpa': float(derived_probs.get(">10 LPA", 0.0)),
            'prob_salary_gt_15_lpa': float(derived_probs.get(">15 LPA", 0.0)),
            'prob_salary_gt_20_lpa': float(derived_probs.get(">20 LPA", 0.0)),
            'prob_salary_gt_25_lpa': float(derived_probs.get(">25 LPA", 0.0)),
            'prob_salary_gt_30_lpa': float(derived_probs.get(">30 LPA", 0.0)),
            'prob_salary_gt_35_lpa': float(derived_probs.get(">35 LPA", 0.0)),
            'prob_salary_gt_40_lpa': float(derived_probs.get(">40 LPA", 0.0)),
            'predicted_job_role': role_name,
            'recommended_companies': recommended_companies,
            'is_low_probability_case': bool(low_probability_report.get('is_low_probability_case')),
            'low_probability_report': low_probability_report,
        }

        return jsonify(response_data), 200

    except Exception as e:
        print(f"[ERROR] Error generating predictions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/predictions/save', methods=['POST'])
def save_predictions():
    """Save predictions to CSV."""
    try:
        data = request.json or {}
        student_id = str(data.get('studentId', '')).strip()
        predictions = data.get('predictions', {})

        if not student_id:
            return jsonify({'success': False, 'error': 'studentId required'}), 400

        # Normalize recommended_companies so join never fails.
        recommended = predictions.get('recommended_companies', [])
        if recommended is None:
            recommended = []
        elif isinstance(recommended, str):
            recommended = [recommended]
        elif not isinstance(recommended, list):
            recommended = [str(recommended)]

        row_data = {
            'student_id': student_id,
            'overall_placement_probability': predictions.get('overall_placement_probability', 0),
            'predicted_salary_lpa': predictions.get('predicted_salary_lpa', 0),
            'salary_range_min_lpa': predictions.get('salary_range_min_lpa', 0),
            'salary_range_mid_lpa': predictions.get('salary_range_mid_lpa', 0),
            'salary_range_max_lpa': predictions.get('salary_range_max_lpa', 0),
            'prob_salary_gt_2_lpa': predictions.get('prob_salary_gt_2_lpa', 0),
            'prob_salary_gt_5_lpa': predictions.get('prob_salary_gt_5_lpa', 0),
            'prob_salary_gt_10_lpa': predictions.get('prob_salary_gt_10_lpa', 0),
            'prob_salary_gt_15_lpa': predictions.get('prob_salary_gt_15_lpa', 0),
            'prob_salary_gt_20_lpa': predictions.get('prob_salary_gt_20_lpa', 0),
            'prob_salary_gt_25_lpa': predictions.get('prob_salary_gt_25_lpa', 0),
            'prob_salary_gt_30_lpa': predictions.get('prob_salary_gt_30_lpa', 0),
            'prob_salary_gt_35_lpa': predictions.get('prob_salary_gt_35_lpa', 0),
            'prob_salary_gt_40_lpa': predictions.get('prob_salary_gt_40_lpa', 0),
            'predicted_job_role': predictions.get('predicted_job_role', ''),
            'recommended_companies': ','.join([str(x) for x in recommended]),
            'is_low_probability_case': bool(predictions.get('is_low_probability_case', False)),
            'low_probability_report_json': json.dumps(predictions.get('low_probability_report') or {}, ensure_ascii=False),
        }

        if os.path.exists(PREDICTIONS_CSV):
            df = pd.read_csv(PREDICTIONS_CSV)
            df['student_id'] = df['student_id'].astype(str)
            idx = df[df['student_id'] == student_id].index
            if len(idx) > 0:
                for key, value in row_data.items():
                    df.at[idx[0], key] = value
            else:
                df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
        else:
            df = pd.DataFrame([row_data])

        # Write atomically with retries to avoid transient file-lock failures on Windows.
        max_retries = 5
        last_err = None
        for attempt in range(max_retries):
            try:
                pred_dir = os.path.dirname(PREDICTIONS_CSV)
                fd, tmp_path = tempfile.mkstemp(prefix='Predicted_Data_', suffix='.tmp', dir=pred_dir)
                os.close(fd)

                df.to_csv(tmp_path, index=False)
                os.replace(tmp_path, PREDICTIONS_CSV)
                return jsonify({'success': True, 'message': 'Predictions saved'}), 200
            except PermissionError as pe:
                last_err = pe
                try:
                    if 'tmp_path' in locals() and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
                # Exponential backoff: 0.2, 0.4, 0.8, 1.6, 3.2 sec
                time.sleep(0.2 * (2 ** attempt))
            except Exception as e:
                try:
                    if 'tmp_path' in locals() and os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
                return jsonify({'error': str(e), 'success': False}), 500

        return jsonify({
            'error': (
                f"Could not write to {PREDICTIONS_CSV}. The file appears to be locked by another process. "
                "Please close any app using this CSV (for example Excel) and try again."
            ),
            'success': False,
            'code': 'CSV_LOCKED',
            'details': str(last_err) if last_err else 'Permission denied'
        }), 423

    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/api/predictions/<student_id>', methods=['GET'])
def get_predictions(student_id):
    """Get student predictions from CSV."""
    try:
        if not os.path.exists(PREDICTIONS_CSV):
            return jsonify({'predictions': None}), 200

        df = pd.read_csv(PREDICTIONS_CSV)
        df['student_id'] = df['student_id'].astype(str)
        match = df[df['student_id'] == str(student_id)]
        if match.empty:
            return jsonify({'predictions': None}), 200

        row = match.iloc[0].to_dict()
        report_raw = row.get('low_probability_report_json')
        if isinstance(report_raw, str) and report_raw.strip():
            try:
                row['low_probability_report'] = json.loads(report_raw)
            except Exception:
                row['low_probability_report'] = None
        elif isinstance(report_raw, dict):
            row['low_probability_report'] = report_raw

        # Backward-compatible upgrade path:
        # If a saved low-probability report was generated before advanced sections were added,
        # rebuild the report at read time from current student/profile + model pipeline.
        is_low = bool(row.get('is_low_probability_case', False)) or _as_float(row.get('overall_placement_probability', 100), 100) < 30.0
        current_report = row.get('low_probability_report')
        if is_low and not _has_advanced_low_report_sections(current_report):
            try:
                student_df = pd.read_csv(STUDENT_CSV)
                student_df['student_id'] = student_df['student_id'].astype(str)
                smatch = student_df[student_df['student_id'] == str(student_id)]
                if not smatch.empty:
                    srow = smatch.iloc[0].to_dict()
                    student_data = {
                        'student_id': str(student_id),
                        'dsa_score': _as_float(srow.get('dsa_score', row.get('dsa_score', 50)), 50),
                        'project_score': _as_float(srow.get('project_score', row.get('project_score', 50)), 50),
                        'aptitude_score': _as_float(srow.get('aptitude_score', row.get('aptitude_score', 50)), 50),
                        'hr_score': _as_float(srow.get('hr_score', row.get('hr_score', 50)), 50),
                        'resume_ats_score': _as_float(srow.get('resume_ats_score', row.get('resume_ats_score', 50)), 50),
                        'cs_fundamentals_score': _as_float(srow.get('cs_fundamentals_score', row.get('cs_fundamentals_score', 50)), 50),
                        'cgpa': _as_float(srow.get('cgpa', row.get('cgpa', 7.0)), 7.0),
                        'hackathon_wins': int(_as_float(srow.get('hackathon_wins', row.get('hackathon_wins', 0)), 0)),
                        'github_projects': int(_as_float(srow.get('github_projects', row.get('github_projects', 0)), 0)),
                        'github_project_links': [],
                    }

                    models_obj = MLModels()
                    if models_obj.load_models():
                        upgraded_report = _build_low_probability_report(
                            student_data,
                            _as_float(row.get('overall_placement_probability', 0), 0),
                            models_obj,
                        )
                        row['low_probability_report'] = upgraded_report
                        row['is_low_probability_case'] = bool(upgraded_report.get('is_low_probability_case', True))
                        row['low_probability_report_json'] = json.dumps(upgraded_report, ensure_ascii=False)
            except Exception as rebuild_err:
                print(f"[WARN] Could not rebuild advanced low-probability report for student {student_id}: {rebuild_err}")

        return jsonify({'predictions': _json_safe(row)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat-history/<student_id>', methods=['GET'])
def get_chat_history(student_id):
    """Get all chat sessions for a student."""
    try:
        sid = _normalize_student_id(student_id)
        store = _read_chat_store()
        student_history = _ensure_student_history(store, sid)

        # Keep active chat valid if stale.
        active = student_history.get('active_chat_id')
        if active and _find_chat(student_history, active) is None:
            sorted_chats = _sort_chats_desc(student_history.get('chats', []))
            student_history['active_chat_id'] = sorted_chats[0]['chat_id'] if sorted_chats else None

        payload = _serialize_student_history(sid, student_history)
        return jsonify(payload), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat-history/<student_id>/new', methods=['POST'])
def create_new_chat(student_id):
    """Create a new chat session for a student and make it active."""
    try:
        sid = _normalize_student_id(student_id)
        body = request.json or {}
        title = str(body.get('title', 'New Chat')).strip() or 'New Chat'

        store = _read_chat_store()
        chat = _create_chat_session(store, sid, title=title)
        _safe_write_chat_store(store)

        student_history = _ensure_student_history(store, sid)
        return jsonify({
            'chat_id': chat['chat_id'],
            'history': _serialize_student_history(sid, student_history)
        }), 201
    except PermissionError:
        return jsonify({'error': 'Chat history file is locked. Please retry.', 'code': 'CHAT_HISTORY_LOCKED'}), 423
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat-history/<student_id>/<chat_id>', methods=['DELETE'])
def delete_chat(student_id, chat_id):
    """Delete one chat session for a student."""
    try:
        sid = _normalize_student_id(student_id)
        store = _read_chat_store()
        student_history = _ensure_student_history(store, sid)

        chats = student_history.get('chats', [])
        remaining = [c for c in chats if str(c.get('chat_id')) != str(chat_id)]

        if len(remaining) == len(chats):
            return jsonify({'error': 'Chat not found'}), 404

        student_history['chats'] = remaining
        if student_history.get('active_chat_id') == str(chat_id):
            sorted_chats = _sort_chats_desc(remaining)
            student_history['active_chat_id'] = sorted_chats[0]['chat_id'] if sorted_chats else None

        _safe_write_chat_store(store)
        return jsonify({'history': _serialize_student_history(sid, student_history)}), 200
    except PermissionError:
        return jsonify({'error': 'Chat history file is locked. Please retry.', 'code': 'CHAT_HISTORY_LOCKED'}), 423
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat-history/<student_id>', methods=['DELETE'])
def clear_student_history(student_id):
    """Delete all chat sessions for a student."""
    try:
        sid = _normalize_student_id(student_id)
        store = _read_chat_store()
        store[sid] = {'active_chat_id': None, 'chats': []}
        _safe_write_chat_store(store)
        return jsonify({'history': _serialize_student_history(sid, store[sid])}), 200
    except PermissionError:
        return jsonify({'error': 'Chat history file is locked. Please retry.', 'code': 'CHAT_HISTORY_LOCKED'}), 423
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<path:filename>', methods=['GET'])
def download_report(filename):
    """Serve generated chatbot reports (PDF)."""
    try:
        if not re.fullmatch(r'[A-Za-z0-9._-]+\.pdf', filename or ''):
            return jsonify({'error': 'Invalid report filename'}), 400

        if not os.path.isdir(REPORTS_DIR):
            return jsonify({'error': 'Reports directory not found'}), 404

        target = os.path.join(REPORTS_DIR, filename)
        if not os.path.isfile(target):
            return jsonify({'error': 'Report not found'}), 404

        return send_from_directory(REPORTS_DIR, filename, as_attachment=True, mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatbot/message', methods=['POST', 'OPTIONS'])
def send_message():
    """Send message to Rasa chatbot"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    try:
        data = request.json or {}
        student_id = data.get('student_id', 'anonymous')
        chat_id = str(data.get('chat_id', '')).strip() or None
        message = data.get('message', '').strip()
        
        print(f"\n[CHATBOT] Received message from {student_id}: {message}")
        
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Persist user message in per-student chat history.
        store = _read_chat_store()
        active_chat_id = _append_chat_message(
            store,
            student_id,
            chat_id,
            sender='user',
            text=message,
            intent='user_message',
            source='user'
        )
        _safe_write_chat_store(store)

        # Prepare Rasa webhook payload
        rasa_payload = {
            'sender': str(student_id),
            'message': message
        }
        
        print(f"[CHATBOT] Sending to Rasa: {rasa_payload}")
        
        answer = ''
        intent = 'info'
        source = 'chatbot'

        rasa_response = requests.post(
            RASA_WEBHOOK_URL,
            json=rasa_payload,
            timeout=10
        )
        
        print(f"[CHATBOT] Rasa response status: {rasa_response.status_code}")
        
        if rasa_response.status_code != 200:
            print(f"[ERROR] Rasa returned status {rasa_response.status_code}")
            answer = 'Sorry, the chatbot is temporarily unavailable.'
            intent = 'error'
            source = 'error'
        else:
            bot_messages = rasa_response.json()
            text_messages = [msg.get('text', '').strip() for msg in bot_messages if msg.get('text')]

            # Some Rasa flows can emit the same report response twice in one turn.
            # Prefer the latest PDF report message when present, otherwise join unique texts.
            report_messages = [t for t in text_messages if 'Downloadable PDF:' in t]
            if report_messages:
                answer = report_messages[-1]
            else:
                unique_messages = []
                seen_norm = set()
                for t in text_messages:
                    norm = ' '.join(t.split())
                    if norm not in seen_norm:
                        seen_norm.add(norm)
                        unique_messages.append(t)
                answer = ' '.join(unique_messages)

            answer = answer if answer else 'I did not understand that. Please try again.'
        
        print(f"[CHATBOT] Bot response: {answer}")

        # Persist bot response to the same chat.
        store = _read_chat_store()
        _append_chat_message(
            store,
            student_id,
            active_chat_id,
            sender='bot',
            text=answer,
            intent=intent,
            source=source
        )
        _safe_write_chat_store(store)
        
        return jsonify({
            'answer': answer,
            'intent': intent,
            'source': source,
            'chat_id': active_chat_id
        }), 200
    
    except requests.exceptions.Timeout:
        print(f"[ERROR] Chatbot request timed out")
        try:
            store = _read_chat_store()
            _append_chat_message(
                store,
                student_id,
                chat_id,
                sender='bot',
                text='The chatbot took too long to respond. Please try again.',
                intent='error',
                source='error'
            )
            _safe_write_chat_store(store)
        except Exception:
            pass
        return jsonify({
            'answer': 'The chatbot took too long to respond. Please try again.',
            'intent': 'error',
            'source': 'error',
            'chat_id': chat_id
        }), 200
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Chatbot request failed: {e}")
        try:
            store = _read_chat_store()
            _append_chat_message(
                store,
                student_id,
                chat_id,
                sender='bot',
                text='Could not connect to the chatbot. Please try again later.',
                intent='error',
                source='error'
            )
            _safe_write_chat_store(store)
        except Exception:
            pass
        return jsonify({
            'answer': 'Could not connect to the chatbot. Please try again later.',
            'intent': 'error',
            'source': 'error',
            'chat_id': chat_id
        }), 200
    
    except Exception as e:
        error_msg = str(e)
        print(f"[EXCEPTION] {type(e).__name__}: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("EduPlus Chatbot API Server Starting...")
    print("="*70)
    print(f"Debug Mode: True")
    print(f"Host: 0.0.0.0")
    print(f"Port: 5000")
    print(f"CORS Enabled: Yes")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
