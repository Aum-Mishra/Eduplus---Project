import argparse
import csv
import os
import re
import time
from datetime import datetime

import requests


def parse_questions_from_catalog(catalog_path: str):
    questions = []
    in_section = False

    with open(catalog_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()

            if text.lower().startswith("## trained intents and their question variations"):
                in_section = True
                continue

            if in_section and text.startswith("## "):
                break

            if not in_section:
                continue

            if text.startswith("- "):
                q = text[2:].strip()
                if q:
                    questions.append(q)

    return questions


def classify(answer: str):
    a = (answer or "").lower().strip()
    if not a:
        return "no_response"
    if "could not" in a or "did not understand" in a:
        return "fallback_or_not_understood"
    if "please mention" in a or "please provide" in a:
        return "clarification_needed"
    return "answered"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=os.path.join("..", "..", "CHATBOT_QUESTION_CATALOG.md"))
    parser.add_argument("--url", default="http://localhost:8001/api/llm-chatbot/message")
    parser.add_argument("--student-id", default="200001")
    parser.add_argument("--delay-ms", type=int, default=40)
    args = parser.parse_args()

    questions = parse_questions_from_catalog(args.catalog)
    if not questions:
        print("No questions parsed from catalog.")
        return

    out_dir = os.path.join("reports", datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    for i, q in enumerate(questions, 1):
        try:
            res = requests.post(
                args.url,
                json={"student_id": args.student_id, "message": q},
                timeout=60,
            )
            data = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            answer = data.get("answer", "")
            status = classify(answer)
            rows.append({
                "index": i,
                "question": q,
                "status": status,
                "intent": data.get("intent", ""),
                "source": data.get("source", ""),
                "answer": answer,
            })
        except Exception as e:
            rows.append({
                "index": i,
                "question": q,
                "status": "request_error",
                "intent": "",
                "source": "",
                "answer": str(e),
            })

        if args.delay_ms > 0:
            time.sleep(args.delay_ms / 1000.0)

    full_csv = os.path.join(out_dir, "results_full.csv")
    with open(full_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "question", "status", "intent", "source", "answer"])
        writer.writeheader()
        writer.writerows(rows)

    failed = [r for r in rows if r["status"] != "answered"]
    failed_csv = os.path.join(out_dir, "unable_to_answer.csv")
    with open(failed_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["index", "question", "status", "intent", "source", "answer"])
        writer.writeheader()
        writer.writerows(failed)

    md_path = os.path.join(out_dir, "unable_to_answer.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Unable To Answer\n\n")
        for r in failed:
            f.write(f"- [{r['status']}] {r['question']}\n")

    summary = {
        "total": len(rows),
        "answered": sum(1 for r in rows if r["status"] == "answered"),
        "clarification_needed": sum(1 for r in rows if r["status"] == "clarification_needed"),
        "fallback_or_not_understood": sum(1 for r in rows if r["status"] == "fallback_or_not_understood"),
        "no_response": sum(1 for r in rows if r["status"] == "no_response"),
        "request_error": sum(1 for r in rows if r["status"] == "request_error"),
    }

    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        import json
        json.dump(summary, f, indent=2)

    print("Audit complete")
    print(f"Output directory: {out_dir}")
    print(summary)


if __name__ == "__main__":
    main()
