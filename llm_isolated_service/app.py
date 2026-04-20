import json
import math
import os
import re
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

STUDENT_CSV = os.path.join(DATA_DIR, "student_profiles_100.csv")
PREDICTIONS_CSV = os.path.join(DATA_DIR, "Predicted_Data.csv")
COMPANY_DB_CSV = os.path.join(DATA_DIR, "company_placement_db.csv")
COMPANY_PROFILES_CSV = os.path.join(DATA_DIR, "company_profiles_with_difficulty.csv")
LEETCODE_DATA_DIR = os.path.join(DATA_DIR, "leetcode-companywise-interview-questions-master")

LLM_CHAT_HISTORY_JSON = os.path.join(DATA_DIR, "llm_chat_history.json")
LLM_REPORTS_DIR = os.path.join(DATA_DIR, "generated_reports_llm")

OLLAMA_BASE_URL = os.getenv("LLM_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("LLM_MODEL_NAME", "mistral")

PREDICTION_UPDATE_TOKEN = "[[PREDICTION_UPDATE_REQUIRED]]"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize_student_id(student_id: Any) -> str:
    return str(student_id).strip()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]

    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
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


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _load_student_row(student_id: str) -> Optional[pd.Series]:
    df = _read_csv(STUDENT_CSV)
    if df.empty or "student_id" not in df.columns:
        return None
    df["student_id"] = df["student_id"].astype(str).str.strip()
    matched = df[df["student_id"] == student_id]
    if matched.empty:
        return None
    return matched.iloc[0]


def _load_prediction_row(student_id: str) -> Optional[pd.Series]:
    df = _read_csv(PREDICTIONS_CSV)
    if df.empty or "student_id" not in df.columns:
        return None
    df["student_id"] = df["student_id"].astype(str).str.strip()
    matched = df[df["student_id"] == student_id]
    if matched.empty:
        return None
    return matched.iloc[0]


def _build_prediction_input_summary(student_row: Optional[pd.Series]) -> Dict[str, Any]:
    required = ["dsa_score", "project_score", "aptitude_score", "hr_score", "resume_ats_score"]
    scores = {}
    missing = []

    for col in required:
        value = _to_float(student_row.get(col) if student_row is not None else None)
        scores[col] = value
        if value is None or value < 0 or value > 100:
            missing.append(col)

    return {
        "available": len(missing) == 0,
        "missing_fields": missing,
        "scores": scores,
    }


def _read_chat_store() -> Dict[str, Any]:
    if not os.path.exists(LLM_CHAT_HISTORY_JSON):
        return {}
    try:
        with open(LLM_CHAT_HISTORY_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe_write_chat_store(store: Dict[str, Any]) -> bool:
    os.makedirs(os.path.dirname(LLM_CHAT_HISTORY_JSON), exist_ok=True)
    last_err = None
    for attempt in range(3):
        fd, tmp_path = tempfile.mkstemp(prefix="llm_chat_history_", suffix=".tmp", dir=os.path.dirname(LLM_CHAT_HISTORY_JSON))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(store, tmp_file, ensure_ascii=False, indent=2)
            os.replace(tmp_path, LLM_CHAT_HISTORY_JSON)
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
    return False


def _build_chat_title(first_text: str) -> str:
    text = str(first_text or "").strip().replace("\n", " ")
    if not text:
        return "New Chat"
    return text[:57] + "..." if len(text) > 60 else text


def _sort_chats_desc(chats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(chats, key=lambda c: c.get("updated_at", ""), reverse=True)


def _ensure_student_history(store: Dict[str, Any], student_id: str) -> Dict[str, Any]:
    sid = _normalize_student_id(student_id)
    if sid not in store or not isinstance(store.get(sid), dict):
        store[sid] = {"active_chat_id": None, "chats": []}
    if "chats" not in store[sid] or not isinstance(store[sid]["chats"], list):
        store[sid]["chats"] = []
    if "active_chat_id" not in store[sid]:
        store[sid]["active_chat_id"] = None
    return store[sid]


def _find_chat(student_history: Dict[str, Any], chat_id: str) -> Optional[Dict[str, Any]]:
    for chat in student_history.get("chats", []):
        if str(chat.get("chat_id")) == str(chat_id):
            return chat
    return None


def _create_chat_session(store: Dict[str, Any], student_id: str, title: Optional[str] = None) -> str:
    now = _now_iso()
    student_history = _ensure_student_history(store, student_id)
    chat_id = str(uuid.uuid4())
    chat = {
        "chat_id": chat_id,
        "title": title or "New Chat",
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    student_history["chats"].insert(0, chat)
    student_history["active_chat_id"] = chat_id
    return chat_id


def _append_chat_message(
    store: Dict[str, Any],
    student_id: str,
    chat_id: Optional[str],
    sender: str,
    text: str,
    intent: Optional[str] = None,
    source: Optional[str] = None,
    value: Any = None,
) -> str:
    now = _now_iso()
    student_history = _ensure_student_history(store, student_id)

    active_chat_id = str(chat_id or student_history.get("active_chat_id") or "").strip()
    chat = _find_chat(student_history, active_chat_id) if active_chat_id else None

    if chat is None:
        active_chat_id = _create_chat_session(store, student_id)
        chat = _find_chat(student_history, active_chat_id)

    message = {
        "sender": sender,
        "text": text,
        "timestamp": now,
        "intent": intent,
        "source": source,
        "value": _json_safe(value),
    }
    chat["messages"].append(message)
    chat["updated_at"] = now

    if sender == "user" and chat.get("title", "New Chat") == "New Chat":
        chat["title"] = _build_chat_title(text)

    student_history["active_chat_id"] = active_chat_id
    return active_chat_id


def _serialize_student_history(student_id: str, student_history: Dict[str, Any]) -> Dict[str, Any]:
    chats = _sort_chats_desc(student_history.get("chats", []))
    return {
        "student_id": _normalize_student_id(student_id),
        "active_chat_id": student_history.get("active_chat_id"),
        "chats": chats,
    }


def _list_leetcode_companies() -> List[str]:
    if not os.path.isdir(LEETCODE_DATA_DIR):
        return []
    companies = []
    for name in os.listdir(LEETCODE_DATA_DIR):
        full = os.path.join(LEETCODE_DATA_DIR, name)
        if os.path.isdir(full):
            companies.append(name.lower())
    return sorted(companies)


def _resolve_leetcode_company(text: str, companies: List[str]) -> Optional[str]:
    q = (text or "").lower()
    for company in companies:
        if company in q or company.replace("-", " ") in q:
            return company
    return None


def _resolve_leetcode_time_file(text: str) -> Tuple[str, str]:
    q = (text or "").lower()
    if any(k in q for k in ["newest", "latest", "recent", "this month", "latest month", "30 day", "30 days", "one month", "1 month"]):
        return "thirty-days.csv", "Last 30 Days"
    if any(k in q for k in ["3 month", "3 months", "three month", "three months", "quarter"]):
        return "three-months.csv", "Last 3 Months"
    if any(k in q for k in ["6 month", "6 months", "six month", "six months", "half year"]):
        return "six-months.csv", "Last 6 Months"
    if any(k in q for k in ["more than six months", "older than six months", "older", "old questions"]):
        return "more-than-six-months.csv", "More Than 6 Months"
    if any(k in q for k in ["all time", "all questions", "complete list", "entire list", "1 year", "one year", "12 month", "12 months", "last year", "past year"]):
        return "all.csv", "All Time"
    return "all.csv", "All Time"


def _extract_leetcode_query_filters(text: str) -> Dict[str, Any]:
    q = (text or "").lower()
    filters = {
        "difficulty": None,
        "top_n": None,
        "sort_by_frequency": False,
        "analytics": False,
        "preparation": False,
        "wants_pdf": False,
    }

    if "easy" in q:
        filters["difficulty"] = "easy"
    elif "medium" in q:
        filters["difficulty"] = "medium"
    elif "hard" in q:
        filters["difficulty"] = "hard"

    top_match = re.search(r"\btop\s+(\d{1,2})\b", q)
    if top_match:
        filters["top_n"] = max(1, min(50, int(top_match.group(1))))

    if any(k in q for k in ["frequent", "frequently", "most common", "common", "trending", "top interview questions"]):
        filters["sort_by_frequency"] = True

    if any(k in q for k in ["how many", "distribution", "percentage", "percent", "mostly"]):
        filters["analytics"] = True

    if any(k in q for k in ["practice", "prepare", "preparation", "crack", "recommend"]):
        filters["preparation"] = True
        filters["sort_by_frequency"] = True
        if filters["top_n"] is None:
            filters["top_n"] = 30

    if any(k in q for k in ["pdf", "report", "download"]):
        filters["wants_pdf"] = True

    return filters


def _to_percent_number(v: Any) -> float:
    cleaned = str(v).replace("%", "").strip()
    try:
        return float(cleaned)
    except Exception:
        return 0.0


def _safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip())
    return slug.strip("-") or "report"


def _format_percent(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(str(value).replace("%", "").strip())
    except Exception:
        return None


def _build_leetcode_pdf_report(
    company: str,
    time_label: str,
    source_csv_path: str,
    questions_df: pd.DataFrame,
    output_pdf_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

    df = questions_df.copy()
    for col in ["Title", "Difficulty", "URL", "Frequency %"]:
        if col not in df.columns:
            df[col] = ""

    df["FrequencyNumeric"] = df["Frequency %"].apply(_to_percent_number)
    df = df.sort_values(["FrequencyNumeric", "Title"], ascending=[False, True]).reset_index(drop=True)

    easy_count = int((df["Difficulty"].astype(str).str.lower() == "easy").sum())
    medium_count = int((df["Difficulty"].astype(str).str.lower() == "medium").sum())
    hard_count = int((df["Difficulty"].astype(str).str.lower() == "hard").sum())

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

    story.append(Paragraph("EduPlus AI Chatbot - LLM Report", styles["Title"]))
    story.append(Paragraph("LeetCode Company-wise Interview Questions", styles["Heading2"]))
    story.append(Spacer(1, 8))

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
    summary_text = (
        f"Company: <b>{company.title()}</b><br/>"
        f"Time Window: <b>{time_label}</b><br/>"
        f"Source File: <b>{os.path.basename(source_csv_path)}</b><br/>"
        f"Generated At (UTC): <b>{generated_at}</b><br/>"
        f"Total Questions: <b>{len(df)}</b><br/>"
        f"Difficulty Split - Easy: <b>{easy_count}</b>, Medium: <b>{medium_count}</b>, Hard: <b>{hard_count}</b>"
    )
    story.append(Paragraph(summary_text, styles["BodyText"]))
    story.append(Spacer(1, 12))

    table_data: List[List[str]] = [["S.No", "Title", "Difficulty", "Frequency", "URL"]]
    for i, row in df.iterrows():
        table_data.append([
            str(i + 1),
            str(row.get("Title", "")),
            str(row.get("Difficulty", "")),
            str(row.get("Frequency %", "")),
            str(row.get("URL", "")),
        ])

    questions_table = Table(table_data, repeatRows=1, colWidths=[0.45 * inch, 2.35 * inch, 0.95 * inch, 0.9 * inch, 2.55 * inch])
    questions_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )

    story.append(questions_table)
    doc.build(story)


def _find_company_name_matches(query: str, company_df: pd.DataFrame) -> List[str]:
    q = (query or "").lower()
    matches: List[str] = []
    if company_df.empty:
        return matches

    names = company_df.get("company_name", pd.Series(dtype=str)).astype(str).str.lower().dropna().unique().tolist()
    for name in names:
        if name and name in q:
            matches.append(name)
    return matches


def _format_company_row(row: pd.Series) -> str:
    return (
        f"- **{row.get('company_name', 'Unknown')}** | Tier: {row.get('company_tier', 'N/A')} | "
        f"Avg Package: {row.get('avg_package_lpa', 'N/A')} LPA | Min CGPA: {row.get('min_cgpa', 'N/A')} | "
        f"Backlogs Allowed: {row.get('backlogs_allowed', row.get('max_backlogs', 'N/A'))}"
    )


def _handle_company_data_query(text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()
    df = _read_csv(COMPANY_DB_CSV)
    if df.empty:
        return None

    # Comparison flow
    if "compare" in q:
        matched = _find_company_name_matches(q, df)
        if len(matched) >= 2:
            c1 = df[df["company_name"].astype(str).str.lower() == matched[0]].head(1)
            c2 = df[df["company_name"].astype(str).str.lower() == matched[1]].head(1)
            if not c1.empty and not c2.empty:
                r1 = c1.iloc[0]
                r2 = c2.iloc[0]
                answer = (
                    f"### Company Comparison: {r1.get('company_name')} vs {r2.get('company_name')}\n\n"
                    f"- {r1.get('company_name')}: Avg Package {r1.get('avg_package_lpa')} LPA, Min CGPA {r1.get('min_cgpa')}, Backlogs Allowed {r1.get('backlogs_allowed')}\n"
                    f"- {r2.get('company_name')}: Avg Package {r2.get('avg_package_lpa')} LPA, Min CGPA {r2.get('min_cgpa')}, Backlogs Allowed {r2.get('backlogs_allowed')}\n"
                )
                return {"text": answer, "intent": "company_comparison", "source": "company_data"}

    # Filter by CGPA
    cgpa_match = re.search(r"(cgpa|gpa)\s*(?:of|=|>|>=|at least)?\s*(\d+(?:\.\d+)?)", q)
    if cgpa_match and any(k in q for k in ["company", "companies", "suitable", "eligible"]):
        cgpa = float(cgpa_match.group(2))
        subset = df[pd.to_numeric(df.get("min_cgpa", pd.Series(dtype=float)), errors="coerce") <= cgpa].copy()
        subset = subset.sort_values(by=["avg_package_lpa"], ascending=False).head(12)
        if subset.empty:
            return {
                "text": f"I could not find companies matching CGPA {cgpa}. Try a broader range.",
                "intent": "company_filter_cgpa",
                "source": "company_data",
            }

        lines = ["### Companies matching your CGPA filter\n"]
        for _, row in subset.iterrows():
            lines.append(_format_company_row(row))
        return {"text": "\n".join(lines), "intent": "company_filter_cgpa", "source": "company_data"}

    # Backlog-related
    if any(k in q for k in ["backlog", "backlogs", "arrear"]):
        subset = df.copy()
        if "backlogs_allowed" in subset.columns:
            subset["backlogs_allowed_num"] = pd.to_numeric(subset["backlogs_allowed"], errors="coerce").fillna(0)
            subset = subset.sort_values(by=["backlogs_allowed_num", "avg_package_lpa"], ascending=[False, False]).head(12)
        else:
            subset = subset.head(12)

        lines = ["### Companies and Backlog Policy Snapshot\n"]
        for _, row in subset.iterrows():
            lines.append(_format_company_row(row))
        return {"text": "\n".join(lines), "intent": "company_backlog_policy", "source": "company_data"}

    # Package query
    if any(k in q for k in ["package", "lpa", "salary", "highest paying", "top paying"]):
        subset = df.copy()
        subset["avg_package_lpa_num"] = pd.to_numeric(subset.get("avg_package_lpa", pd.Series(dtype=float)), errors="coerce")
        subset = subset.sort_values(by=["avg_package_lpa_num"], ascending=False).head(12)

        lines = ["### Top Companies by Average Package\n"]
        for _, row in subset.iterrows():
            lines.append(_format_company_row(row))
        return {"text": "\n".join(lines), "intent": "company_package_query", "source": "company_data"}

    # Single company detail
    matched = _find_company_name_matches(q, df)
    if matched:
        company = matched[0]
        rows = df[df["company_name"].astype(str).str.lower() == company]
        if not rows.empty:
            row = rows.iloc[0]
            details = [
                f"### {row.get('company_name', company.title())}",
                "",
                f"- Tier: {row.get('company_tier', 'N/A')}",
                f"- Average Package: {row.get('avg_package_lpa', 'N/A')} LPA",
                f"- Maximum Package: {row.get('max_package_lpa', 'N/A')} LPA",
                f"- Minimum CGPA: {row.get('min_cgpa', 'N/A')}",
                f"- Allowed Departments: {row.get('allowed_departments', 'N/A')}",
                f"- Required Skills: {row.get('required_skills', 'N/A')}",
                f"- Backlogs Allowed: {row.get('backlogs_allowed', row.get('max_backlogs', 'N/A'))}",
                f"- Hiring Roles: {row.get('hiring_roles_description', row.get('job_role_notes', 'N/A'))}",
            ]
            return {"text": "\n".join(details), "intent": "company_single_detail", "source": "company_data"}

    return None


def _extract_salary_threshold_lpa(text: str) -> Optional[int]:
    q = (text or "").lower()
    m = re.search(r"(\d{1,2})\s*(?:\+|plus|\s*lpa|\s*lakh|\s*lakhs)", q)
    if m:
        try:
            return int(m.group(1))
        except Exception:
            return None
    return None


def _handle_prediction_probability_query(student_row: Optional[pd.Series], prediction_row: Optional[pd.Series], text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()
    if prediction_row is None:
        return None

    probability_markers = ["probability", "chance", "likely", "likelihood", "odds", "possible"]
    salary_markers = ["lpa", "salary", "package"]
    if not any(m in q for m in probability_markers) or not any(m in q for m in salary_markers):
        return None

    threshold = _extract_salary_threshold_lpa(q)
    if threshold is None:
        return None

    supported = [2, 5, 10, 15, 20, 25, 30, 35, 40]
    if threshold not in supported:
        nearest = min(supported, key=lambda x: abs(x - threshold))
    else:
        nearest = threshold

    col = f"prob_salary_gt_{nearest}_lpa"
    prob_value = _format_percent(prediction_row.get(col))
    predicted_salary = _to_float(prediction_row.get("predicted_salary_lpa"))

    if prob_value is None:
        return None

    tone = ""
    if prob_value < 25:
        tone = (
            "Your current probability is low right now, but this is absolutely improvable. "
            "With consistent preparation, targeted practice, and better interview readiness, you can push this up significantly."
        )
    elif prob_value < 60:
        tone = (
            "Your probability is in a moderate zone. With focused effort over the next few months, "
            "you can move into a stronger range."
        )
    else:
        tone = "You are in a good zone already. If you keep momentum, you can realistically convert high-package opportunities."

    answer = (
        f"### Probability for {nearest}+ LPA\n\n"
        f"Your current estimated probability of getting **more than {nearest} LPA** is **{prob_value:.2f}%**.\n\n"
        f"{tone}\n\n"
        + (f"Your current predicted salary is **{predicted_salary:.2f} LPA**.\n" if predicted_salary is not None else "")
        + "Focus next on DSA consistency, project depth, resume quality, and mock interviews to improve this probability."
    )

    return {
        "text": answer,
        "intent": "salary_probability_query",
        "source": "prediction_data",
        "value": {
            "requested_threshold_lpa": threshold,
            "resolved_threshold_lpa": nearest,
            "probability_percent": prob_value,
            "column_used": col,
        },
    }


def _handle_company_profile_query(text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()
    df = _read_csv(COMPANY_DB_CSV)
    if df.empty:
        return None

    if "company_name" not in df.columns:
        return None

    matches = _find_company_name_matches(q, df)
    if not matches:
        return None

    company = matches[0]
    row_df = df[df["company_name"].astype(str).str.lower() == company].head(1)
    if row_df.empty:
        return None
    row = row_df.iloc[0]

    def val(key: str, default: str = "N/A") -> str:
        v = row.get(key, default)
        if v is None:
            return default
        s = str(v).strip()
        return s if s else default

    round_details = []
    for i in range(1, 5):
        rn = val(f"round{i}_name", "")
        rf = val(f"round{i}_focus", "")
        rd = val(f"round{i}_duration_min", "")
        if rn and rn != "N/A":
            dur = f" ({rd} min)" if rd and rd != "N/A" else ""
            focus = f" - Focus: {rf}" if rf and rf != "N/A" else ""
            round_details.append(f"Round {i}: {rn}{dur}{focus}")

    if any(k in q for k in ["how many rounds", "no of rounds", "number of rounds", "rounds are there"]):
        answer = (
            f"### {val('company_name')} Interview Rounds\n\n"
            f"{val('company_name')} usually has **{len(round_details)} rounds** in this dataset.\n\n"
            + ("\n".join(f"- {r}" for r in round_details) if round_details else "Round details are not available.")
        )
        return {"text": answer, "intent": "company_round_count", "source": "company_round_data"}

    if any(k in q for k in ["first round", "1st round", "round 1"]):
        rname = val("round1_name")
        rfocus = val("round1_focus")
        rdur = val("round1_duration_min")
        prep = val("prep_dsa_topics")
        answer = (
            f"### First Round for {val('company_name')}\n\n"
            f"Your first round is typically **{rname}**"
            + (f" for about **{rdur} minutes**.\n" if rdur != "N/A" else ".\n")
            + (f"Main focus: **{rfocus}**.\n\n" if rfocus != "N/A" else "\n")
            + "How you can prepare:\n"
            + f"- Practice these DSA topics: **{prep}**\n"
            + "- Solve timed company-pattern questions and revise core concepts."
        )
        return {"text": answer, "intent": "company_first_round", "source": "company_round_data"}

    if any(k in q for k in ["fourth round", "4th round", "round 4"]):
        rname = val("round4_name")
        rfocus = val("round4_focus")
        rdur = val("round4_duration_min")
        answer = (
            f"### Fourth Round for {val('company_name')}\n\n"
            f"Round 4 is typically **{rname}**"
            + (f" for about **{rdur} minutes**.\n" if rdur != "N/A" else ".\n")
            + (f"Primary focus: **{rfocus}**." if rfocus != "N/A" else "Focus details are not available.")
        )
        return {"text": answer, "intent": "company_fourth_round", "source": "company_round_data"}

    if any(k in q for k in ["what are the topics", "topics i should prepare", "prepare topics", "how should i prepare", "prep topics"]):
        topics = [
            ("DSA", val("prep_dsa_topics")),
            ("System Design", val("prep_system_design_topics")),
            ("OOPS", val("prep_oops_topics")),
            ("DBMS", val("prep_dbms_topics")),
            ("HR", val("prep_hr_topics")),
        ]
        lines = [f"### Preparation Topics for {val('company_name')}", ""]
        for label, topic in topics:
            lines.append(f"- **{label}:** {topic}")
        return {"text": "\n".join(lines), "intent": "company_prep_topics", "source": "company_round_data"}

    # Generic company profile fallback for other company-specific asks.
    lines = [
        f"### {val('company_name')} Company Profile",
        "",
        f"- Tier: **{val('company_tier')}**",
        f"- Average Package: **{val('avg_package_lpa')} LPA**",
        f"- Max Package: **{val('max_package_lpa')} LPA**",
        f"- Minimum CGPA: **{val('min_cgpa')}**",
        f"- Allowed Departments: **{val('allowed_departments')}**",
        f"- Required Skills: **{val('required_skills')}**",
        f"- Backlogs Allowed: **{val('backlogs_allowed', val('max_backlogs'))}**",
        f"- Hiring Intensity: **{val('hiring_intensity')}**",
    ]
    if round_details:
        lines.append("\n#### Interview Rounds")
        lines.extend(f"- {r}" for r in round_details)

    return {"text": "\n".join(lines), "intent": "company_profile_detail", "source": "company_round_data"}


def _handle_prediction_query(student_row: Optional[pd.Series], prediction_row: Optional[pd.Series], text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()
    wants_prediction = any(k in q for k in [
        "placement probability",
        "my prediction",
        "predicted salary",
        "salary range",
        "predicted job role",
        "recommended companies",
        "my placement",
        "placement chances",
    ])

    if not wants_prediction:
        return None

    if prediction_row is None:
        msg = (
            "I could not find saved prediction outputs for your profile yet. "
            "Please run the Placement Probability flow first to generate predictions.\n\n"
            f"{PREDICTION_UPDATE_TOKEN}"
        )
        return {"text": msg, "intent": "missing_prediction_data", "source": "prediction_data"}

    overall = prediction_row.get("overall_placement_probability", "N/A")
    salary = prediction_row.get("predicted_salary_lpa", "N/A")
    rmin = prediction_row.get("salary_range_min_lpa", "N/A")
    rmax = prediction_row.get("salary_range_max_lpa", "N/A")
    role = prediction_row.get("predicted_job_role", "N/A")
    companies = prediction_row.get("recommended_companies", "N/A")

    explain_mode = any(k in q for k in ["explain", "meaning", "why", "understand", "interpret"])

    try:
        overall_num = float(str(overall).replace("%", "").strip())
    except Exception:
        overall_num = None

    confidence_line = ""
    if overall_num is not None:
        if overall_num >= 85:
            confidence_line = "You are currently in a strong position for placements."
        elif overall_num >= 70:
            confidence_line = "You are in a good position, and focused preparation can improve your chances further."
        elif overall_num >= 50:
            confidence_line = "You are in a moderate zone right now, with clear scope to improve outcomes."
        else:
            confidence_line = "You are currently in a lower-probability zone, so a structured preparation plan is important."

    if explain_mode:
        answer = (
            "### Your Placement Prediction (Explained)\n\n"
            f"Based on your current profile, your placement probability is **{overall}%**. {confidence_line}\n\n"
            f"Your predicted package is around **{salary} LPA**, with a likely range of **{rmin} to {rmax} LPA**. "
            f"Your current profile aligns most with the **{role}** role.\n\n"
            "Recommended companies from your current profile are:\n"
            f"- **{companies}**\n\n"
            "To improve this prediction further, start with:\n"
            "- Improve your DSA consistency with timed practice and mock rounds.\n"
            "- Strengthen one or two projects with measurable impact and clean documentation.\n"
            "- Update ATS-friendly resume keywords based on your target role.\n"
        )
    else:
        answer = (
            "### Your Placement Prediction Summary\n\n"
            f"You currently have an estimated placement probability of **{overall}%**.\n"
            f"Your predicted salary is **{salary} LPA**, with an expected range of **{rmin} to {rmax} LPA**.\n"
            f"Your most likely job role is **{role}**.\n"
            f"Recommended companies for your present profile: **{companies}**.\n"
        )

    return {"text": answer, "intent": "prediction_summary", "source": "prediction_data", "value": _json_safe(prediction_row.to_dict())}


def _extract_salary_goal_lpa(text: str) -> Optional[float]:
    q = (text or "").lower()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lakh)", q)
    if match:
        try:
            return float(match.group(1))
        except Exception:
            return None
    return None


def _handle_salary_goal_query(student_row: Optional[pd.Series], prediction_row: Optional[pd.Series], text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()

    if any(k in q for k in ["probability", "chance", "likely", "likelihood", "odds"]):
        return None

    salary_goal = _extract_salary_goal_lpa(q)
    if salary_goal is None:
        return None

    intent_markers = [
        "can i get",
        "can i achieve",
        "how to get",
        "what i need to do",
        "what should i do",
        "how can i",
        "reach",
        "target",
        "more than",
        "above",
    ]
    if not any(marker in q for marker in intent_markers):
        return None

    predicted_salary = None
    if prediction_row is not None:
        predicted_salary = _to_float(prediction_row.get("predicted_salary_lpa"))

    prob_gt_20 = _format_percent(prediction_row.get("prob_salary_gt_20_lpa")) if prediction_row is not None else None
    prob_gt_25 = _format_percent(prediction_row.get("prob_salary_gt_25_lpa")) if prediction_row is not None else None
    prob_gt_15 = _format_percent(prediction_row.get("prob_salary_gt_15_lpa")) if prediction_row is not None else None

    cgpa = _to_float(student_row.get("cgpa")) if student_row is not None else None
    dsa = _to_float(student_row.get("dsa_score")) if student_row is not None else None
    project = _to_float(student_row.get("project_score")) if student_row is not None else None
    ats = _to_float(student_row.get("resume_ats_score")) if student_row is not None else None
    aptitude = _to_float(student_row.get("aptitude_score")) if student_row is not None else None
    hr = _to_float(student_row.get("hr_score")) if student_row is not None else None

    eligible_companies = []
    df = _read_csv(COMPANY_DB_CSV)
    if not df.empty and cgpa is not None and "min_cgpa" in df.columns and "avg_package_lpa" in df.columns:
        temp = df.copy()
        temp["min_cgpa_num"] = pd.to_numeric(temp["min_cgpa"], errors="coerce")
        temp["avg_package_lpa_num"] = pd.to_numeric(temp["avg_package_lpa"], errors="coerce")
        subset = temp[(temp["avg_package_lpa_num"] >= salary_goal) & (temp["min_cgpa_num"] <= cgpa)]
        subset = subset.sort_values(by=["avg_package_lpa_num"], ascending=False).head(5)
        for _, row in subset.iterrows():
            eligible_companies.append(f"{row.get('company_name')} ({row.get('avg_package_lpa')} LPA, min CGPA {row.get('min_cgpa')})")

    # Use company profile dataset to extract required skills for 20+ LPA targets.
    target_companies = []
    aggregated_skills: List[str] = []
    profile_df = _read_csv(COMPANY_PROFILES_CSV)
    if not profile_df.empty and "avg_package_lpa" in profile_df.columns and "company_name" in profile_df.columns:
        p = profile_df.copy()
        p["avg_package_lpa_num"] = pd.to_numeric(p["avg_package_lpa"], errors="coerce")
        p["min_cgpa_num"] = pd.to_numeric(p.get("min_cgpa", pd.Series(dtype=float)), errors="coerce")
        top = p[p["avg_package_lpa_num"] >= salary_goal].sort_values(by=["avg_package_lpa_num"], ascending=False).head(8)

        for _, row in top.iterrows():
            company_name = str(row.get("company_name", "Unknown")).strip()
            avg_pkg = row.get("avg_package_lpa", "N/A")
            min_c = row.get("min_cgpa", "N/A")
            required_skills = str(row.get("required_skills", "N/A")).strip()
            backlogs_allowed = str(row.get("backlogs_allowed", "N/A")).strip()

            cgpa_gap = None
            min_c_num = _to_float(min_c)
            if cgpa is not None and min_c_num is not None:
                cgpa_gap = round(min_c_num - cgpa, 2)

            skill_tokens = [s.strip() for s in re.split(r"[,/|]", required_skills) if s and s.strip() and s.strip().lower() != "n/a"]
            for token in skill_tokens:
                if token not in aggregated_skills:
                    aggregated_skills.append(token)

            target_companies.append(
                {
                    "company_name": company_name,
                    "avg_package_lpa": _to_float(avg_pkg) if _to_float(avg_pkg) is not None else avg_pkg,
                    "min_cgpa": min_c,
                    "cgpa_gap": cgpa_gap,
                    "required_skills": required_skills,
                    "backlogs_allowed": backlogs_allowed,
                }
            )

    gap_line = ""
    if predicted_salary is not None:
        if predicted_salary >= salary_goal:
            gap_line = f"Good news: your current predicted package (**{predicted_salary:.2f} LPA**) is already near/above your target of **{salary_goal:.1f} LPA**."
        else:
            gap = salary_goal - predicted_salary
            gap_line = (
                f"Right now your predicted package is **{predicted_salary:.2f} LPA**, so you need roughly **{gap:.2f} LPA** more to consistently hit **{salary_goal:.1f} LPA** roles."
            )
    else:
        gap_line = f"Your current prediction data is unavailable, but you can still target **{salary_goal:.1f} LPA** with focused preparation."

    probability_assessment = ""
    if prob_gt_20 is not None:
        if prob_gt_20 < 20:
            probability_assessment = (
                f"Your current estimated probability of crossing **20 LPA** is **{prob_gt_20:.2f}%**, "
                "which is low right now. This is not a final outcome; with focused effort, you can improve it."
            )
        elif prob_gt_20 < 50:
            probability_assessment = (
                f"Your current estimated probability of crossing **20 LPA** is **{prob_gt_20:.2f}%**, "
                "which is moderate. A strong preparation sprint can push this higher."
            )
        else:
            probability_assessment = (
                f"Your current estimated probability of crossing **20 LPA** is **{prob_gt_20:.2f}%**, "
                "which is a strong base to build on."
            )

    tips = []
    if dsa is not None and dsa < 70:
        tips.append("Raise your DSA score toward 75+ with company-focused problem patterns and timed mocks.")
    else:
        tips.append("Maintain strong DSA consistency through weekly contests and mock interviews.")

    if project is not None and project < 70:
        tips.append("Upgrade your top 2 projects to production-grade quality (deployment, metrics, architecture clarity).")
    else:
        tips.append("Show depth in your projects with measurable impact and clean design decisions.")

    if ats is not None and ats < 75:
        tips.append("Improve your resume ATS score by aligning keywords with high-package role job descriptions.")
    else:
        tips.append("Keep your resume tailored for target companies and role-specific skills.")

    tips.append("Apply strategically to high-package companies where your CGPA and skills match eligibility.")

    company_block = ""
    if eligible_companies:
        company_block = "\n\nBased on your current CGPA, realistic high-package targets include:\n" + "\n".join(f"- {c}" for c in eligible_companies)

    data_snapshot = []
    if predicted_salary is not None:
        data_snapshot.append(f"- Predicted Salary: **{predicted_salary:.2f} LPA**")
    if prob_gt_15 is not None:
        data_snapshot.append(f"- Probability >15 LPA: **{prob_gt_15:.2f}%**")
    if prob_gt_20 is not None:
        data_snapshot.append(f"- Probability >20 LPA: **{prob_gt_20:.2f}%**")
    if prob_gt_25 is not None:
        data_snapshot.append(f"- Probability >25 LPA: **{prob_gt_25:.2f}%**")

    why_low_lines = []
    if prob_gt_20 is not None and prob_gt_20 < 20:
        why_low_lines.append("Your current >20 LPA probability is low, so this goal needs a significant profile jump.")
    if dsa is not None and dsa < 70:
        why_low_lines.append(f"Your DSA score (**{dsa:.1f}**) is below the typical bar for top-package roles.")
    if project is not None and project < 70:
        why_low_lines.append(f"Your project score (**{project:.1f}**) indicates room to improve project depth and impact.")
    if ats is not None and ats < 75:
        why_low_lines.append(f"Your ATS score (**{ats:.1f}**) can limit shortlist conversion for premium roles.")
    if not why_low_lines:
        why_low_lines.append("Your base profile is decent, but top-package roles still demand stronger consistency and interview depth.")

    day30 = [
        "Solve 80-100 focused DSA problems (arrays, strings, trees, graphs, DP).",
        "Rebuild your resume for ATS and target role keywords.",
        "Finalize 1 flagship project with clear impact metrics and deployment.",
    ]
    day60 = [
        "Complete 8-10 timed mock interviews (DSA + CS fundamentals + HR).",
        "Finish system design and OOPS/DBMS revision for interview rounds.",
        "Upgrade one more project to production quality and add measurable outcomes.",
    ]
    day90 = [
        "Run company-specific preparation sprints for 20+ LPA target companies.",
        "Apply strategically to aligned roles and track conversion stage-by-stage.",
        "Iterate weak areas from mock feedback every week.",
    ]

    company_lines = []
    for c in target_companies[:6]:
        gap_txt = ""
        if c.get("cgpa_gap") is not None:
            if c["cgpa_gap"] > 0:
                gap_txt = f"CGPA gap: +{c['cgpa_gap']}"
            else:
                gap_txt = "CGPA gap: Eligible"
        else:
            gap_txt = "CGPA gap: Unknown"
        company_lines.append(
            f"- **{c.get('company_name')}** | Avg Package: **{c.get('avg_package_lpa')} LPA** | Min CGPA: **{c.get('min_cgpa')}** | {gap_txt} | Skills: {c.get('required_skills')}"
        )

    skills_focus = aggregated_skills[:18]
    skills_line = ", ".join(skills_focus) if skills_focus else "No clear skill list found in company profile data."

    answer = (
        f"### Reaching {salary_goal:.1f}+ LPA\n\n"
        "#### Reality Check\n"
        + f"{gap_line}\n"
        + (f"{probability_assessment}\n" if probability_assessment else "")
        + ("You can improve this with disciplined effort and a focused plan.\n" if prob_gt_20 is not None and prob_gt_20 < 20 else "")
        + "\n#### Data Used\n"
        + ("\n".join(data_snapshot) if data_snapshot else "- Prediction probability fields are currently unavailable")
        + "\n\n#### Why Low Right Now\n"
        + "\n".join(f"- {line}" for line in why_low_lines)
        + "\n\n#### 30/60/90 Day Action Plan\n"
        + "**Next 30 Days**\n"
        + "\n".join(f"- {x}" for x in day30)
        + "\n\n**Day 31-60**\n"
        + "\n".join(f"- {x}" for x in day60)
        + "\n\n**Day 61-90**\n"
        + "\n".join(f"- {x}" for x in day90)
        + "\n\n#### Target Companies and Eligibility Gap\n"
        + ("\n".join(company_lines) if company_lines else "- No 20+ LPA company profile rows were found.")
        + "\n\n#### Skills You Should Prepare (From 20+ LPA Company Profiles)\n"
        + f"- {skills_line}"
    )

    return {
        "text": answer,
        "intent": "salary_goal_guidance",
        "source": "prediction_and_company_data",
        "value": {
            "salary_goal_lpa": salary_goal,
            "predicted_salary_lpa": predicted_salary,
            "prob_salary_gt_15_lpa": prob_gt_15,
            "prob_salary_gt_20_lpa": prob_gt_20,
            "prob_salary_gt_25_lpa": prob_gt_25,
            "eligible_high_package_companies": eligible_companies,
            "target_companies": target_companies,
            "aggregated_required_skills": skills_focus,
            "action_plan": {
                "day_30": day30,
                "day_60": day60,
                "day_90": day90,
            },
        },
    }


def _handle_score_guidance_query(student_row: Optional[pd.Series], text: str) -> Optional[Dict[str, Any]]:
    if student_row is None:
        return None

    q = (text or "").lower()
    score_intent_markers = [
        "score",
        "improve",
        "guidance",
        "increase",
        "boost",
        "tips",
        "advice",
        "weak",
        "low",
        "high",
        "better",
    ]

    # Avoid hijacking content/intelligence requests (for example LeetCode question/PDF asks)
    # and only respond when the user is explicitly asking for score improvement guidance.
    if not any(marker in q for marker in score_intent_markers):
        return None

    score_keys = {
        "dsa": "dsa_score",
        "leetcode": "dsa_score",
        "github": "project_score",
        "project": "project_score",
        "aptitude": "aptitude_score",
        "ats": "resume_ats_score",
        "resume": "resume_ats_score",
        "hr": "hr_score",
    }

    matched_col = None
    matched_key = None
    for key, col in score_keys.items():
        if key in q:
            matched_col = col
            matched_key = key
            break

    if not matched_col:
        return None

    val = _to_float(student_row.get(matched_col))
    if val is None:
        return {
            "text": (
                f"I could not find your {matched_col} in the profile data. "
                "Please update the score in the Placement Probability flow and try again."
            ),
            "intent": "missing_score",
            "source": "student_profile",
        }

    guidance = []
    if val < 40:
        guidance.append("Focus on fundamentals first; target weekly practice consistency.")
    elif val < 70:
        guidance.append("You are in a moderate zone; improve quality and consistency to reach the next band.")
    else:
        guidance.append("Strong score; maintain momentum with advanced practice and mocks.")

    if matched_col == "dsa_score":
        guidance.append("Prioritize arrays, strings, trees, graphs, and dynamic programming patterns.")
    elif matched_col == "project_score":
        guidance.append("Strengthen project architecture, documentation, and measurable impact.")
    elif matched_col == "hr_score":
        guidance.append("Use STAR structure and quantify outcomes in your answers.")

    answer = (
        f"### {matched_key.title()} Guidance\n\n"
        f"- Current Score: **{val:.1f}/100**\n"
        + "\n".join(f"- {tip}" for tip in guidance)
    )
    return {"text": answer, "intent": "score_guidance", "source": "student_profile"}


def _handle_leetcode_company_query(text: str) -> Optional[Dict[str, Any]]:
    q = (text or "").lower()
    markers = [
        "leetcode",
        "interview questions",
        "company questions",
        "questions asked",
        "coding questions",
        "practice questions",
        "top questions",
        "generate pdf",
    ]
    if not any(k in q for k in markers):
        return None

    companies = _list_leetcode_companies()
    if not companies:
        return {"text": "LeetCode company-wise dataset is not available right now.", "intent": "leetcode_company_questions", "source": "leetcode_dataset"}

    company = _resolve_leetcode_company(q, companies)
    if not company:
        return {
            "text": "Please mention a company name for LeetCode interview questions (for example: amazon, google, microsoft).",
            "intent": "leetcode_company_questions",
            "source": "leetcode_dataset",
        }

    csv_file_name, time_label = _resolve_leetcode_time_file(q)
    csv_path = os.path.join(LEETCODE_DATA_DIR, company, csv_file_name)
    if not os.path.exists(csv_path):
        fallback = os.path.join(LEETCODE_DATA_DIR, company, "all.csv")
        if not os.path.exists(fallback):
            return {
                "text": f"I could not find question data for {company.title()} right now.",
                "intent": "leetcode_company_questions",
                "source": "leetcode_dataset",
            }
        csv_path = fallback
        csv_file_name = "all.csv"
        time_label = "All Time"

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {
            "text": f"I could not read the dataset due to: {e}",
            "intent": "leetcode_company_questions",
            "source": "leetcode_dataset",
        }

    if df.empty:
        return {
            "text": f"No questions found for {company.title()} in {time_label}.",
            "intent": "leetcode_company_questions",
            "source": "leetcode_dataset",
        }

    for col in ["Title", "Difficulty", "URL", "Frequency %"]:
        if col not in df.columns:
            df[col] = ""

    filters = _extract_leetcode_query_filters(q)
    df["FrequencyNumeric"] = df["Frequency %"].apply(_to_percent_number)

    if filters["difficulty"]:
        df = df[df["Difficulty"].astype(str).str.lower() == filters["difficulty"]]

    if filters["sort_by_frequency"]:
        df = df.sort_values(["FrequencyNumeric", "Title"], ascending=[False, True])

    if filters["top_n"] is not None:
        df = df.head(int(filters["top_n"]))

    df = df.reset_index(drop=True)

    if df.empty:
        return {
            "text": "No questions matched this filter set. Try removing difficulty or top-N constraints.",
            "intent": "leetcode_company_questions",
            "source": "leetcode_dataset",
        }

    easy_count = int((df["Difficulty"].astype(str).str.lower() == "easy").sum())
    medium_count = int((df["Difficulty"].astype(str).str.lower() == "medium").sum())
    hard_count = int((df["Difficulty"].astype(str).str.lower() == "hard").sum())

    top_preview = []
    for i, row in df.head(10).iterrows():
        top_preview.append(f"{i + 1}. {row.get('Title', '')} ({row.get('Difficulty', 'N/A')}, {row.get('Frequency %', 'N/A')})")

    response_lines = [
        f"### LeetCode Questions for {company.title()} ({time_label})",
        "",
        f"- Total Questions Returned: **{len(df)}**",
        f"- Difficulty Split: Easy **{easy_count}**, Medium **{medium_count}**, Hard **{hard_count}**",
    ]

    if filters["difficulty"]:
        response_lines.append(f"- Difficulty Filter Applied: **{filters['difficulty'].title()}**")
    if filters["top_n"] is not None:
        response_lines.append(f"- Top-N Applied: **{filters['top_n']}**")

    response_lines.append("\n#### Top Question Preview")
    response_lines.extend(f"- {line}" for line in top_preview)

    download_url = None
    if filters["wants_pdf"] or "download" in q or "report" in q:
        os.makedirs(LLM_REPORTS_DIR, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        report_name = f"llm_leetcode_{_safe_slug(company)}_{_safe_slug(csv_file_name.replace('.csv', ''))}_{ts}_{uuid.uuid4().hex[:8]}.pdf"
        report_path = os.path.join(LLM_REPORTS_DIR, report_name)

        try:
            _build_leetcode_pdf_report(company=company, time_label=time_label, source_csv_path=csv_path, questions_df=df, output_pdf_path=report_path)
            download_url = f"http://localhost:{os.getenv('LLM_SERVER_PORT', '8001')}/api/llm-reports/{report_name}"
            response_lines.append(f"\nDownloadable PDF: {download_url}")
        except Exception as e:
            response_lines.append(f"\nI could not generate the PDF report due to: {e}")

    if filters["preparation"]:
        response_lines.append("\n#### Preparation Mode Suggestions")
        response_lines.append("- Start with high-frequency easy/medium questions.")
        response_lines.append("- Track patterns (two pointers, sliding window, graph traversal, DP).")
        response_lines.append("- Revisit hard questions after mastering foundational variants.")

    return {
        "text": "\n".join(response_lines),
        "intent": "leetcode_company_questions",
        "source": "leetcode_dataset",
        "value": {
            "company": company,
            "time_label": time_label,
            "count": len(df),
            "easy": easy_count,
            "medium": medium_count,
            "hard": hard_count,
            "download_url": download_url,
        },
    }


def _build_student_context_text(student_row: Optional[pd.Series], prediction_row: Optional[pd.Series]) -> str:
    lines = []

    if student_row is not None:
        lines.append("Student Profile Context:")
        for key in [
            "name",
            "branch",
            "cgpa",
            "dsa_score",
            "project_score",
            "aptitude_score",
            "hr_score",
            "resume_ats_score",
            "cs_fundamentals_score",
        ]:
            if key in student_row.index:
                lines.append(f"- {key}: {student_row.get(key)}")

    if prediction_row is not None:
        lines.append("Prediction Context:")
        for key in [
            "overall_placement_probability",
            "predicted_salary_lpa",
            "salary_range_min_lpa",
            "salary_range_max_lpa",
            "predicted_job_role",
            "recommended_companies",
        ]:
            if key in prediction_row.index:
                lines.append(f"- {key}: {prediction_row.get(key)}")

    return "\n".join(lines)


def _call_ollama_mistral(user_text: str, student_context: str) -> Tuple[str, str]:
    system_prompt = (
        "You are EduPlus AI Assistant. "
        "Give accurate, concise, and well-formatted answers in natural human language. "
        "Address the student directly as 'you'. "
        "Do not refer to the student as 'they' or 'them'. "
        "Use bullet points when listing items, paragraphs for explanation, and markdown headers when useful. "
        "Never fabricate exact company policy numbers if not in context; say data unavailable."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Context:\n{student_context}"},
            {"role": "user", "content": user_text},
        ],
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        message = data.get("message", {})
        content = str(message.get("content", "")).strip()
        if content:
            return content, "llm_mistral"
        return "I could not produce an LLM response right now.", "llm_mistral"
    except Exception:
        fallback = (
            "I could not reach local Mistral right now.\n\n"
            "- Ensure Ollama is running.\n"
            f"- Ensure model '{OLLAMA_MODEL}' is available.\n"
            "- Then retry your question."
        )
        return fallback, "llm_fallback"


def _build_humanization_payload(
    student_id: str,
    user_text: str,
    response_obj: Dict[str, Any],
    student_row: Optional[pd.Series],
    prediction_row: Optional[pd.Series],
) -> Dict[str, Any]:
    student_data = _json_safe(student_row.to_dict()) if student_row is not None else {}
    prediction_data = _json_safe(prediction_row.to_dict()) if prediction_row is not None else {}

    # Keep a compact, high-value snapshot for style-preserving rewrite.
    key_prediction = {}
    for key in [
        "overall_placement_probability",
        "predicted_salary_lpa",
        "salary_range_min_lpa",
        "salary_range_max_lpa",
        "predicted_job_role",
        "recommended_companies",
        "prob_salary_gt_10_lpa",
        "prob_salary_gt_15_lpa",
        "prob_salary_gt_20_lpa",
        "prob_salary_gt_25_lpa",
    ]:
        if key in prediction_data:
            key_prediction[key] = prediction_data.get(key)

    # For high-salary probability/salary-goal intents, avoid leaking generic recommended companies
    # into rewrite so the model focuses on probability evidence and realistic guidance.
    if response_obj.get("intent") in {"salary_goal_guidance", "salary_probability_query"}:
        key_prediction.pop("recommended_companies", None)

    return {
        "student_id": student_id,
        "user_question": user_text,
        "intent": response_obj.get("intent"),
        "source": response_obj.get("source"),
        "base_answer": response_obj.get("text", ""),
        "base_value": _json_safe(response_obj.get("value")),
        "student_profile": {
            "name": student_data.get("name"),
            "branch": student_data.get("branch"),
            "cgpa": student_data.get("cgpa"),
            "dsa_score": student_data.get("dsa_score"),
            "project_score": student_data.get("project_score"),
            "aptitude_score": student_data.get("aptitude_score"),
            "hr_score": student_data.get("hr_score"),
            "resume_ats_score": student_data.get("resume_ats_score"),
        },
        "prediction_snapshot": key_prediction,
    }


def _humanize_response_with_llm(
    student_id: str,
    user_text: str,
    response_obj: Dict[str, Any],
    student_row: Optional[pd.Series],
    prediction_row: Optional[pd.Series],
) -> Dict[str, Any]:
    if response_obj.get("intent") == "llm_processing_error":
        return response_obj
    if response_obj.get("intent") == "salary_goal_guidance":
        # Keep deterministic structured coaching format unchanged.
        return response_obj

    payload = _build_humanization_payload(student_id, user_text, response_obj, student_row, prediction_row)

    system_prompt = (
        "You rewrite assistant answers for students in natural, human, personalized language. "
        "Write as if speaking directly to one student: always use 'you'. "
        "Never use 'they/them' for the student. "
        "Keep all factual numbers, percentages, salary ranges, company names, and URLs exactly accurate. "
        "Do not invent data that is not in the provided payload. "
        "Do not claim the student has a good chance when probability is low. "
        "If prob_salary_gt_20_lpa is below 20, clearly say the current chance is low but improvable with effort. "
        "Always include a short 'Data Used' section with the key extracted metrics when available. "
        "If a PDF/download URL exists, keep it visible in the final response. "
        "Return concise markdown with short paragraphs and bullets where useful."
    )

    user_prompt = (
        "Rewrite the answer based on this JSON payload.\n"
        "Output only the final student-facing answer text.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    request_payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=request_payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = str(data.get("message", {}).get("content", "")).strip()
        if not content:
            return response_obj

        rewritten = dict(response_obj)

        # Guardrail for salary-probability realism.
        value_obj = response_obj.get("value") or {}
        prob20 = _format_percent(value_obj.get("prob_salary_gt_20_lpa"))
        if prob20 is not None and prob20 < 20:
            content = re.sub(r"(?i)good chance", "currently low chance", content)
            content = re.sub(r"(?i)high chance", "currently low chance", content)

        # Force an explicit data snapshot section for salary-goal/probability intents.
        if response_obj.get("intent") in {"salary_goal_guidance", "salary_probability_query"}:
            data_lines = []
            ps = _to_float(value_obj.get("predicted_salary_lpa"))
            p15 = _format_percent(value_obj.get("prob_salary_gt_15_lpa"))
            p20 = _format_percent(value_obj.get("prob_salary_gt_20_lpa"))
            p25 = _format_percent(value_obj.get("prob_salary_gt_25_lpa"))
            if ps is not None:
                data_lines.append(f"- Predicted Salary: **{ps:.2f} LPA**")
            if p15 is not None:
                data_lines.append(f"- Probability >15 LPA: **{p15:.2f}%**")
            if p20 is not None:
                data_lines.append(f"- Probability >20 LPA: **{p20:.2f}%**")
            if p25 is not None:
                data_lines.append(f"- Probability >25 LPA: **{p25:.2f}%**")

            if data_lines:
                content = content.strip() + "\n\n#### Data Used From Your Prediction\n" + "\n".join(data_lines)

        rewritten["text"] = content
        rewritten["source"] = f"{response_obj.get('source', 'deterministic')}_humanized"
        return rewritten
    except Exception:
        return response_obj


def _build_final_response(student_id: str, text: str) -> Dict[str, Any]:
    student_row = _load_student_row(student_id)
    prediction_row = _load_prediction_row(student_id)

    # 1) Deterministic handlers for parity features
    result = _handle_prediction_query(student_row, prediction_row, text)
    if result:
        return result

    # Route LeetCode questions and PDF requests before score guidance
    # so queries like "top amazon leetcode questions" are not misclassified.
    result = _handle_leetcode_company_query(text)
    if result:
        return result

    result = _handle_prediction_probability_query(student_row, prediction_row, text)
    if result:
        return result

    result = _handle_salary_goal_query(student_row, prediction_row, text)
    if result:
        return result

    result = _handle_company_profile_query(text)
    if result:
        return result

    company_result = _handle_company_data_query(text)
    if company_result:
        return company_result

    result = _handle_score_guidance_query(student_row, text)
    if result:
        return result

    # 2) LLM fallback with context
    context_text = _build_student_context_text(student_row, prediction_row)
    llm_text, llm_source = _call_ollama_mistral(text, context_text)

    return {
        "text": llm_text,
        "intent": "llm_conversational",
        "source": llm_source,
    }


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Isolated LLM service is running"}), 200


@app.route("/api/auth/login", methods=["POST"])
def login_student():
    try:
        payload = request.json or {}
        raw_student_id = str(payload.get("student_id", "")).strip()
        raw_password = str(payload.get("password", "")).strip()

        if not raw_student_id or not raw_password:
            return jsonify({"success": False, "message": "Student ID and password are required"}), 400

        if raw_password != raw_student_id:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

        student_row = _load_student_row(raw_student_id)
        if student_row is None:
            return jsonify({"success": False, "message": "Student ID not found"}), 404

        student_name = str(student_row.get("name", f"Student {raw_student_id}"))
        return jsonify(
            {
                "success": True,
                "student_id": int(raw_student_id) if raw_student_id.isdigit() else raw_student_id,
                "name": student_name,
                "student": _json_safe(student_row.to_dict()),
            }
        ), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/student/<student_id>", methods=["GET"])
def get_student(student_id: str):
    sid = _normalize_student_id(student_id)
    row = _load_student_row(sid)
    if row is None:
        return jsonify({"exists": False, "message": "Student ID not found", "student_id": sid}), 404

    prediction_row = _load_prediction_row(sid)
    return jsonify(
        {
            "exists": True,
            "name": str(row.get("name", "Unknown")),
            "id": sid,
            "student_id": sid,
            "data": _json_safe(row.to_dict()),
            "prediction_input": _build_prediction_input_summary(row),
            "lastPrediction": _json_safe(prediction_row.to_dict()) if prediction_row is not None else None,
        }
    ), 200


@app.route("/api/llm-chat-history/<student_id>", methods=["GET"])
def get_chat_history(student_id: str):
    sid = _normalize_student_id(student_id)
    store = _read_chat_store()
    student_history = _ensure_student_history(store, sid)
    return jsonify(_serialize_student_history(sid, student_history)), 200


@app.route("/api/llm-chat-history/<student_id>/new", methods=["POST"])
def create_new_chat(student_id: str):
    sid = _normalize_student_id(student_id)
    payload = request.json or {}
    title = str(payload.get("title", "New Chat")).strip() or "New Chat"

    store = _read_chat_store()
    chat_id = _create_chat_session(store, sid, title=title)
    _safe_write_chat_store(store)

    student_history = _ensure_student_history(store, sid)
    return jsonify({"chat_id": chat_id, "history": _serialize_student_history(sid, student_history)}), 200


@app.route("/api/llm-chat-history/<student_id>/<chat_id>", methods=["DELETE"])
def delete_chat(student_id: str, chat_id: str):
    sid = _normalize_student_id(student_id)
    store = _read_chat_store()
    student_history = _ensure_student_history(store, sid)

    chats = student_history.get("chats", [])
    remaining = [c for c in chats if str(c.get("chat_id")) != str(chat_id)]
    if len(remaining) == len(chats):
        return jsonify({"error": "Chat not found"}), 404

    student_history["chats"] = remaining
    if student_history.get("active_chat_id") == str(chat_id):
        sorted_chats = _sort_chats_desc(remaining)
        student_history["active_chat_id"] = sorted_chats[0]["chat_id"] if sorted_chats else None

    _safe_write_chat_store(store)
    return jsonify({"history": _serialize_student_history(sid, student_history)}), 200


@app.route("/api/llm-chat-history/<student_id>", methods=["DELETE"])
def clear_history(student_id: str):
    sid = _normalize_student_id(student_id)
    store = _read_chat_store()
    store[sid] = {"active_chat_id": None, "chats": []}
    _safe_write_chat_store(store)
    return jsonify({"history": _serialize_student_history(sid, store[sid])}), 200


@app.route("/api/llm-reports/<path:filename>", methods=["GET"])
def download_llm_report(filename: str):
    try:
        if not re.fullmatch(r"[A-Za-z0-9._-]+\.pdf", filename or ""):
            return jsonify({"error": "Invalid report filename"}), 400

        if not os.path.isdir(LLM_REPORTS_DIR):
            return jsonify({"error": "Reports directory not found"}), 404

        target = os.path.join(LLM_REPORTS_DIR, filename)
        if not os.path.isfile(target):
            return jsonify({"error": "Report not found"}), 404

        return send_from_directory(LLM_REPORTS_DIR, filename, as_attachment=True, mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/llm-chatbot/message", methods=["POST"])
def llm_message():
    try:
        payload = request.json or {}
        student_id = _normalize_student_id(payload.get("student_id", ""))
        chat_id = str(payload.get("chat_id", "")).strip() or None
        message = str(payload.get("message", "")).strip()

        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        if not message:
            return jsonify({"error": "message cannot be empty"}), 400

        if _load_student_row(student_id) is None:
            return jsonify({"error": "Student ID not found"}), 404

        store = _read_chat_store()
        active_chat_id = _append_chat_message(
            store,
            student_id,
            chat_id,
            sender="user",
            text=message,
            intent="user_message",
            source="user",
        )

        # Persist the user message immediately so it never disappears on transient failures.
        _safe_write_chat_store(store)

        student_row = _load_student_row(student_id)
        prediction_row = _load_prediction_row(student_id)

        try:
            response_obj = _build_final_response(student_id, message)
        except Exception:
            response_obj = {
                "text": (
                    "I hit an internal issue while processing that question, but your message is saved. "
                    "Please try again."
                ),
                "intent": "llm_processing_error",
                "source": "llm_fallback",
            }

        response_obj = _humanize_response_with_llm(
            student_id=student_id,
            user_text=message,
            response_obj=response_obj,
            student_row=student_row,
            prediction_row=prediction_row,
        )

        bot_answer = response_obj.get("text", "I did not understand that. Please try again.")

        active_chat_id = _append_chat_message(
            store,
            student_id,
            active_chat_id,
            sender="bot",
            text=bot_answer,
            intent=response_obj.get("intent"),
            source=response_obj.get("source"),
            value=response_obj.get("value"),
        )

        _safe_write_chat_store(store)

        return (
            jsonify(
                {
                    "answer": bot_answer,
                    "intent": response_obj.get("intent", "llm_conversational"),
                    "source": response_obj.get("source", "llm_mistral"),
                    "value": _json_safe(response_obj.get("value")),
                    "student_id": student_id,
                    "chat_id": active_chat_id,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("LLM_SERVER_PORT", "8001"))
    app.run(host="0.0.0.0", port=port, debug=True)
