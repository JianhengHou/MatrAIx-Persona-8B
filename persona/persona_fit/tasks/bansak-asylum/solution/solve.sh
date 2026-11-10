#!/bin/bash
# Harness check only (no persona): first option / scale midpoint for every question.
set -euo pipefail
mkdir -p /app/output
cat > /app/output/survey_result.json <<'JSON'
{
  "instrument": {
    "id": "persona_fit_bansak_asylum",
    "title": "Bansak, Hainmueller & Hangartner asylum conjoint"
  },
  "answers": [
    {
      "questionId": "q001",
      "prompt": "Paar 1: Welchem der beiden Antragsteller soll Asyl gew\u00e4hrt werden?",
      "value": "a"
    }
  ],
  "trajectory": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_started",
      "context": {
        "instrumentId": "persona_fit_bansak_asylum"
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
        "instrumentId": "persona_fit_bansak_asylum",
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
        "instrumentId": "persona_fit_bansak_asylum",
        "questionId": "q001",
        "questionType": "single_choice"
      },
      "outcome": {
        "questionId": "q001",
        "value": "a"
      }
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_completed",
      "context": {
        "instrumentId": "persona_fit_bansak_asylum"
      },
      "outcome": {
        "valid": true
      }
    }
  ]
}
JSON
