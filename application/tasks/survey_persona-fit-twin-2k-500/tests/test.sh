#!/usr/bin/env bash
# Persona-fit ground-truth verifier: test_state.py writes reward.txt itself.
set -euo pipefail

# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/verifier_env.sh"

python3 "${TESTS_DIR}/test_state.py"
