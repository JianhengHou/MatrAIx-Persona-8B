#!/bin/bash
# Harness check only (no persona): first option / scale midpoint for every question.
set -euo pipefail
mkdir -p /app/output
cat > /app/output/survey_result.json <<'JSON'
{
  "instrument": {
    "id": "persona_fit_twin_2k_500",
    "title": "Twin-2K-500 held-out survey items"
  },
  "answers": [
    {
      "questionId": "q001",
      "prompt": "Choose between: (example gamble A) and (example gamble B).",
      "value": "o1"
    }
  ],
  "trajectory": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_started",
      "context": {
        "instrumentId": "persona_fit_twin_2k_500"
      },
      "outcome": {
        "status": "started"
      }
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "assistant",
      "action": "ask_question",
      "context": {
        "instrumentId": "persona_fit_twin_2k_500",
        "questionId": "q001",
        "questionType": "single_choice"
      },
      "outcome": {}
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "user",
      "action": "answer_question",
      "context": {
        "instrumentId": "persona_fit_twin_2k_500",
        "questionId": "q001",
        "questionType": "single_choice"
      },
      "outcome": {
        "questionId": "q001",
        "value": "o1"
      }
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_completed",
      "context": {
        "instrumentId": "persona_fit_twin_2k_500"
      },
      "outcome": {
        "valid": true
      }
    }
  ]
}
JSON
