#!/bin/bash
# Harness check only (no persona): first option / scale midpoint for every question.
set -euo pipefail
mkdir -p /app/output
cat > /app/output/survey_result.json <<'JSON'
{
  "instrument": {
    "id": "persona_fit_movielens_1m",
    "title": "MovieLens 1M ratings"
  },
  "answers": [
    {
      "questionId": "q001",
      "prompt": "Movie 1: how many stars (1-5) do you give Example Comedy?",
      "value": 3
    }
  ],
  "trajectory": [
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_started",
      "context": {
        "instrumentId": "persona_fit_movielens_1m"
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
        "instrumentId": "persona_fit_movielens_1m",
        "questionId": "q001",
        "questionType": "likert"
      },
      "outcome": {}
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "user",
      "action": "answer_question",
      "context": {
        "instrumentId": "persona_fit_movielens_1m",
        "questionId": "q001",
        "questionType": "likert"
      },
      "outcome": {
        "questionId": "q001",
        "value": 3
      }
    },
    {
      "timestamp": "2026-01-01T00:00:00Z",
      "actor": "system",
      "action": "survey_completed",
      "context": {
        "instrumentId": "persona_fit_movielens_1m"
      },
      "outcome": {
        "valid": true
      }
    }
  ]
}
JSON
