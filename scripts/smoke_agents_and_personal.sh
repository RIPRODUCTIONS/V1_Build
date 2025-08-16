#!/usr/bin/env bash
set -euo pipefail

HDR=$( [ -n "${INTERNAL_API_KEY:-}" ] && echo "-H X-API-Key: ${INTERNAL_API_KEY}" )

# Agents registry
curl -sS http://127.0.0.1:8000/ai/agents/registry | cat

# Agent run (planner)
AGENT_JSON=$(mktemp)
printf '%s' '{"agent":"planner","goal":"plan osint autopilot","context":{}}' > "$AGENT_JSON"
curl -sS -X POST http://127.0.0.1:8000/ai/agents/run -H 'Content-Type: application/json' --data-binary @"$AGENT_JSON" | cat

echo

# Personal research quick run
PR_JSON=$(mktemp)
printf '%s' '{"query":"site:reddit.com threat intel best practices"}' > "$PR_JSON"
curl -sS -X POST http://127.0.0.1:8000/personal/run/research_assistant -H 'Content-Type: application/json' -H "X-API-Key: ${INTERNAL_API_KEY}" --data-binary @"$PR_JSON" | cat

echo


