import argparse
import csv
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


FALLBACK_MARKERS = [
    "i didn't understand",
    "i did not understand",
    "i didn't quite catch",
    "i did not quite catch",
    "please ask one of the template-based queries",
    "sorry",
]

CLARIFICATION_MARKERS = [
    "which company",
    "please mention the company",
    "please specify which company",
    "please provide your student id",
    "without knowing who you are",
]


@dataclass
class QuestionItem:
    intent: str
    question: str


@dataclass
class AuditResult:
    intent: str
    question: str
    normalized_question: str
    status: str
    reason: str
    response_text: str
    http_status: int
    error: str


def normalize_question(text: str) -> str:
    """Convert markdown entity annotations like [Amazon](company) to plain text."""
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_catalog_questions(catalog_path: Path) -> List[QuestionItem]:
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found: {catalog_path}")

    lines = catalog_path.read_text(encoding="utf-8").splitlines()

    in_question_section = False
    current_intent = "unknown"
    items: List[QuestionItem] = []

    for raw in lines:
        line = raw.strip()

        if line.startswith("## ") and "Trained Intents And Their Question Variations" in line:
            in_question_section = True
            continue

        if in_question_section and line.startswith("## ") and "Trained Intents And Their Question Variations" not in line:
            break

        if not in_question_section:
            continue

        if line.startswith("### "):
            current_intent = line[4:].strip()
            continue

        if line.startswith("- "):
            question = line[2:].strip()
            if question:
                items.append(QuestionItem(intent=current_intent, question=question))

    return items


def post_to_rasa(rasa_url: str, sender: str, message: str, timeout_sec: int) -> Tuple[int, List[dict], Optional[str]]:
    payload = {"sender": sender, "message": message}
    try:
        resp = requests.post(rasa_url, json=payload, timeout=timeout_sec)
        if resp.status_code != 200:
            return resp.status_code, [], f"HTTP {resp.status_code}: {resp.text[:300]}"
        data = resp.json() if resp.text.strip() else []
        if not isinstance(data, list):
            return resp.status_code, [], "Unexpected non-list response payload"
        return resp.status_code, data, None
    except requests.RequestException as exc:
        return 0, [], str(exc)


def extract_response_text(messages: List[dict]) -> str:
    texts: List[str] = []
    for msg in messages:
        if isinstance(msg, dict):
            txt = msg.get("text")
            if isinstance(txt, str) and txt.strip():
                texts.append(txt.strip())
    return "\n".join(texts).strip()


def classify_response(response_text: str, err: Optional[str]) -> Tuple[str, str]:
    if err:
        return "request_error", "request failed"

    if not response_text:
        return "no_response", "empty bot response"

    low = response_text.lower()

    if any(marker in low for marker in FALLBACK_MARKERS):
        return "fallback_or_not_understood", "fallback detected"

    if any(marker in low for marker in CLARIFICATION_MARKERS):
        return "clarification_needed", "bot asked for missing context"

    return "answered", "meaningful response"


def ensure_report_dir(base_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base_dir / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def write_reports(out_dir: Path, results: List[AuditResult]) -> None:
    full_csv = out_dir / "results_full.csv"
    fail_csv = out_dir / "unable_to_answer.csv"
    fail_md = out_dir / "unable_to_answer.md"
    summary_json = out_dir / "summary.json"

    with full_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()) if results else [
            "intent", "question", "normalized_question", "status", "reason", "response_text", "http_status", "error"
        ])
        writer.writeheader()
        for row in results:
            writer.writerow(asdict(row))

    unable = [r for r in results if r.status in {"fallback_or_not_understood", "no_response", "request_error"}]
    with fail_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["intent", "question", "status", "reason", "response_text", "error"])
        writer.writeheader()
        for r in unable:
            writer.writerow({
                "intent": r.intent,
                "question": r.question,
                "status": r.status,
                "reason": r.reason,
                "response_text": r.response_text,
                "error": r.error,
            })

    with fail_md.open("w", encoding="utf-8") as f:
        f.write("# Unable To Answer\n\n")
        if not unable:
            f.write("All tested questions returned non-fallback responses.\n")
        else:
            for idx, r in enumerate(unable, 1):
                f.write(f"{idx}. [{r.intent}] {r.question}\n")
                f.write(f"   - status: {r.status}\n")
                f.write(f"   - reason: {r.reason}\n")
                if r.response_text:
                    f.write(f"   - response: {r.response_text[:300]}\n")
                if r.error:
                    f.write(f"   - error: {r.error}\n")
                f.write("\n")

    counts: Dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    summary = {
        "total": len(results),
        "status_counts": counts,
        "unable_to_answer_count": len(unable),
        "generated_at": datetime.now().isoformat(),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run_audit(
    catalog_path: Path,
    rasa_url: str,
    student_id: str,
    mode: str,
    timeout_sec: int,
    delay_ms: int,
    dry_run: bool,
) -> List[AuditResult]:
    questions = parse_catalog_questions(catalog_path)
    if not questions:
        raise RuntimeError("No questions extracted from catalog.")

    results: List[AuditResult] = []

    if dry_run:
        for q in questions:
            nq = normalize_question(q.question)
            results.append(AuditResult(
                intent=q.intent,
                question=q.question,
                normalized_question=nq,
                status="answered",
                reason="dry-run",
                response_text="",
                http_status=0,
                error="",
            ))
        return results

    shared_sender = f"auditor-session-{int(time.time())}"

    if mode == "session":
        # Register student once for entire session.
        post_to_rasa(rasa_url, shared_sender, f"My student ID is {student_id}", timeout_sec)

    for i, q in enumerate(questions, start=1):
        nq = normalize_question(q.question)
        sender = shared_sender if mode == "session" else f"auditor-{int(time.time())}-{i}"

        if mode == "isolated":
            # Register student for each isolated conversation.
            post_to_rasa(rasa_url, sender, f"My student ID is {student_id}", timeout_sec)

        code, data, err = post_to_rasa(rasa_url, sender, nq, timeout_sec)
        response_text = extract_response_text(data)
        status, reason = classify_response(response_text, err)

        results.append(AuditResult(
            intent=q.intent,
            question=q.question,
            normalized_question=nq,
            status=status,
            reason=reason,
            response_text=response_text,
            http_status=code,
            error=err or "",
        ))

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Standalone Rasa chatbot question auditor")
    parser.add_argument("--catalog", required=True, help="Path to CHATBOT_QUESTION_CATALOG.md")
    parser.add_argument("--rasa-url", default="http://localhost:5005/webhooks/rest/webhook", help="Rasa REST webhook URL")
    parser.add_argument("--student-id", default="200001", help="Known valid student ID used for test setup")
    parser.add_argument("--mode", choices=["isolated", "session"], default="isolated", help="isolated = each question independent, session = one continuous chat")
    parser.add_argument("--timeout-sec", type=int, default=20, help="HTTP timeout per request")
    parser.add_argument("--delay-ms", type=int, default=0, help="Delay between questions in milliseconds")
    parser.add_argument("--report-dir", default="reports", help="Base report directory")
    parser.add_argument("--dry-run", action="store_true", help="Parse catalog and generate reports without calling Rasa")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    catalog_path = Path(args.catalog).resolve()
    report_dir = Path(args.report_dir).resolve()

    results = run_audit(
        catalog_path=catalog_path,
        rasa_url=args.rasa_url,
        student_id=args.student_id,
        mode=args.mode,
        timeout_sec=args.timeout_sec,
        delay_ms=args.delay_ms,
        dry_run=args.dry_run,
    )

    out_dir = ensure_report_dir(report_dir)
    write_reports(out_dir, results)

    unable = [r for r in results if r.status in {"fallback_or_not_understood", "no_response", "request_error"}]
    print(f"Total tested: {len(results)}")
    print(f"Unable to answer: {len(unable)}")
    print(f"Report folder: {out_dir}")


if __name__ == "__main__":
    main()
