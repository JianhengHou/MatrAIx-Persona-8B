#!/bin/bash
# Harness check only (no persona): first option / scale midpoint for every question.
set -euo pipefail
mkdir -p /app/output
cat > /app/output/survey_result.json <<'JSON'
{
  "instrument": {
    "id": "persona_fit_eb_nerd",
    "title": "EB-NeRD news clicks"
  },
  "answers": [
    {
      "questionId": "q001",
      "prompt": "Artikel 1, sektion sport: Danmark vinder \u2014 Sen aften i Parken.  Ville du \u00e5bne den?",
      "value": "yes"
    }
  ],
  "trajectory": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_started",
      "context": {
        "instrumentId": "persona_fit_eb_nerd"
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
        "instrumentId": "persona_fit_eb_nerd",
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
        "instrumentId": "persona_fit_eb_nerd",
        "questionId": "q001",
        "questionType": "single_choice"
      },
      "outcome": {
        "questionId": "q001",
        "value": "yes"
      }
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_completed",
      "context": {
        "instrumentId": "persona_fit_eb_nerd"
      },
      "outcome": {
        "valid": true
      }
    }
  ]
}
JSON
