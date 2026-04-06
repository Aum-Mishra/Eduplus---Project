# Chatbot Question Auditor (Standalone)

This is a standalone test program to validate whether your Rasa chatbot can answer all questions listed in `CHATBOT_QUESTION_CATALOG.md`.

It is intentionally separate from the main system and can run on a different server/environment.

## What It Does

- Parses all utterance lines under the `Trained Intents And Their Question Variations` section.
- Sends each question to a Rasa REST webhook endpoint.
- Optionally initializes each test with a valid student ID (default: `200001`).
- Captures output text, classifies status, and generates reports.
- Produces a dedicated list of questions the bot could not answer.

## Output Files

When run, it writes files under `reports/<timestamp>/`:

- `results_full.csv`: Full per-question results
- `unable_to_answer.csv`: Questions marked as not answered
- `unable_to_answer.md`: Human-readable failure list
- `summary.json`: Aggregated metrics

## Status Classification

- `answered`: Bot returned meaningful output
- `clarification_needed`: Bot asked for missing context (for example company name)
- `fallback_or_not_understood`: Bot returned generic fallback
- `no_response`: Empty response payload
- `request_error`: Request failed/timeout/HTTP error

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run Example

```powershell
python run_audit.py \
  --catalog "..\..\CHATBOT_QUESTION_CATALOG.md" \
  --rasa-url "http://localhost:5005/webhooks/rest/webhook" \
  --student-id "200001" \
  --mode isolated \
  --delay-ms 50
```

## Notes

- Use `--mode isolated` to test each question independently.
- Use `--mode session` to test one continuous chat session.
- Use `--dry-run` to validate parsing without calling Rasa.
