#!/bin/bash
# agentic_ai.sh - Main CLI entry point for Twinhead Dragon

echo "🐉 Kali GPT Agent Console"
echo "─────────────────────────"

while true; do
  read -p "> " user_input
  [[ "$user_input" == "exit" ]] && break

  echo "[🧠 Reasoning & Planning...]"
  json_output=$(python3 reasoning_node.py "$user_input")

  echo "$json_output" | jq -r '"[REASONING] " + .reasoning'
  echo "$json_output" | jq -r '"[TOOL] " + .tool'
  echo "$json_output" | jq -r '"[COMMAND] " + .command'

  echo "[⚙️ EXECUTING TOOL INSIDE KALI...]"
  exec_output=$(ssh kali@192.168.56.10 "python3 /opt/agentic/executor_node.py '$json_output'")

  echo "[📄 RESULTS]"
  echo "$exec_output" | jq

done
