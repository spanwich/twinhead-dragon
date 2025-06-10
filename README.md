# Twinhead Dragon (Temporary Name)

## IMPORTANT: This is for research purpose only.
## Overview

This system enables autonomous offensive security operations against ICS targets (like OpenPLC) using Kali Linux tools. The architecture separates reasoning (agentic decision-making) from execution (actual tool usage) and operates via a CLI interface for human evaluators.

---

## 🧠 Agentic Pattern: ReAct + Toolformer Hybrid

### ReAct

* Reasoning about each step
* Decides next best action

### Toolformer Style

* Uses structured JSON to define what tool to use, with parameters
* Designed to invoke registered tools programmatically

---

## 📐 System Architecture

```text
┌───────────────────────────────────────────────┐
│         🧠 Reasoning & Planning Node          │  (Outside Kali)
│───────────────────────────────────────────────│
│  • CLI Interface                              │
│  • Uses GPT-4 API (Kali GPT prompt style)     │
│  • Outputs structured plans (JSON)            │
└───────────────────────────────────────────────┘
                     │
                     ▼ SSH / Docker Exec / RPC
┌───────────────────────────────────────────────┐
│           ⚙️ Executor Node (Inside Kali)       │
│───────────────────────────────────────────────│
│  • Receives command JSON or Bash              │
│  • Executes tools (nmap, modbus-cli, etc.)    │
│  • Returns result: stdout, logs, artifacts     │
└───────────────────────────────────────────────┘
                     ▲
               Output / Evidence
                     │
┌───────────────────────────────────────────────┐
│              📜 Evaluator Module              │
│───────────────────────────────────────────────│
│  • CLI logs and results                       │
│  • Human evaluator assesses performance       │
└───────────────────────────────────────────────┘
```

---

## 🔧 Components

### Reasoning Node (outside Kali)

* Runs LLM queries to GPT-4
* Uses prompt template that enforces structured responses
* Operates CLI-only

### Executor Node (inside Kali Linux)

* Receives structured commands
* Executes with optional sandboxing (e.g., Firejail, Docker)
* Logs output and errors

### Communication Bridge

* Options: `ssh`, `docker exec`, `gRPC`, `named pipes`
* Bi-directional: commands go in, results go out

### CLI Interface

* User enters natural language queries
* Receives reasoning, plan, execution, results
* Example:

  ```
  > Enumerate ports in a way that's hard to detect
  [PLAN] Use nmap with stealth scan: nmap -sS -T1 -Pn ...
  [RESULTS] 3 hosts with open ports. Output saved to ...
  ```

---

## 🧪 Design Goals

| Feature            | Priority | Description                              |
| ------------------ | -------- | ---------------------------------------- |
| Autonomy           | ✅ High   | Agent decides and executes               |
| Real-world tooling | ✅ High   | Uses actual Kali tools                   |
| Modular execution  | ✅ High   | New tools pluggable                      |
| CLI-only interface | ✅ High   | No web/UI needed                         |
| Human evaluation   | ✅ High   | Results reviewed by human                |
| Secure separation  | ✅ High   | Reasoning outside, execution inside Kali |

---

## 📦 Output Schema (from Reasoning Node)

```json
{
  "reasoning": "To avoid detection, we'll use a slow SYN scan",
  "tool": "nmap",
  "command": "nmap -sS -T1 -Pn 192.168.56.0/24 -oN stealth_scan.txt",
  "next": "Analyze results for web services on open ports"
}
```

---

## 🛠 Tool Registry Example (Executor Node)

| Tool       | Command Template                           |
| ---------- | ------------------------------------------ |
| nmap       | nmap \[args]                               |
| modbus-cli | modbus \[read/write] \[target] \[register] |
| gobuster   | gobuster dir -u \[url] -w \[wordlist]      |

---

## 🔐 Security Notes

* Executor is sandboxed (AppArmor, Firejail, nsjail)
* Kali VM/container is isolated from production network
* Logs are retained for all agent decisions and actions
* Despite root-level tool usage, sandboxing prevents unrestricted system-wide access and enforces operational constraints
* Supports dry-run execution for safe testing and debugging
* All communications validated, encoded, and timestamped
* Limited execution permissions and user scoping

---

## ✅ Functional Requirements

* Accept user input as natural language commands via CLI
* Translate input into structured tool invocation plans using GPT-based Reasoning Node
* Deliver planned command(s) to Executor Node over a secure bridge
* Run Kali-based tools within a sandbox environment and return structured results
* Store logs, artifacts, and metrics for evaluation
* Support interactive and one-shot CLI interaction modes
* Enforce timeouts, logging, and controlled retries

---

## ❎ Non-Functional Requirements

* Secure communication and execution with sandboxing and isolation techniques
* System must maintain availability for long-running agent sessions
* Execution must be traceable and auditable through comprehensive logging
* Design should be modular to support new tools and protocol integrations
* CLI interface must remain responsive and human-readable
* No graphical interface or network-exposed APIs by design

---

## 📄 Reasoning Node Implementation (Python)

Below is the initial scaffold of `reasoning_node.py`, responsible for converting user queries into structured plans using the OpenAI GPT API.

```python
#!/usr/bin/env python3

import openai
import json
import sys
import os

# Set your API key securely
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt template
SYSTEM_PROMPT = """
You are Kali GPT, an autonomous reasoning agent for offensive security. 
Given a natural-language request, you must produce a structured JSON plan 
to execute a Kali Linux tool.

Respond ONLY with JSON, using this schema:
{
  "reasoning": "...",
  "tool": "...",
  "command": "...",
  "next": "..."
}
Only respond with JSON. Do not include explanations outside the JSON object.
"""

def generate_plan(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.3,
            max_tokens=512,
        )

        output = response['choices'][0]['message']['content']
        plan = json.loads(output)
        return plan

    except json.JSONDecodeError:
        print("[ERROR] Model response is not valid JSON.")
        print(output)
        sys.exit(1)

    except Exception as e:
        print(f"[FATAL] OpenAI API call failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reasoning_node.py \"<task description>\"")
        sys.exit(1)

    task_description = sys.argv[1]
    plan = generate_plan(task_description)
    print(json.dumps(plan, indent=2))
```

---

## 🛠 Executor Node Implementation (Python)

Below is the initial scaffold for `executor_node.py`, responsible for securely executing structured command input inside Kali Linux:

```python
#!/usr/bin/env python3

import json
import subprocess
import sys
import os
import datetime

LOG_DIR = "/var/log/agentic_ai"
os.makedirs(LOG_DIR, exist_ok=True)

# Read JSON input from stdin or file
if len(sys.argv) < 2:
    print("Usage: executor_node.py '<json_file_or_raw_input>'")
    sys.exit(1)

try:
    raw_input = sys.argv[1]
    # If it's a filepath, load JSON from file
    if os.path.exists(raw_input):
        with open(raw_input) as f:
            task = json.load(f)
    else:
        task = json.loads(raw_input)

    tool = task.get("tool")
    command = task.get("command")
    timeout = task.get("timeout", 60)  # Default timeout

    if not tool or not command:
        raise ValueError("Missing required fields: 'tool' or 'command'")

    print(f"[INFO] Running tool: {tool}")
    print(f"[CMD] {command}")

    result = subprocess.run(command, shell=True, capture_output=True, timeout=timeout, text=True)

    timestamp = datetime.datetime.utcnow().isoformat()
    log_file = os.path.join(LOG_DIR, f"{tool}_{timestamp}.log")
    with open(log_file, "w") as f:
        f.write(result.stdout)

    response = {
        "status": "success" if result.returncode == 0 else "error",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
        "artifacts": [log_file]
    }

    print(json.dumps(response, indent=2))

except subprocess.TimeoutExpired:
    print(json.dumps({
        "status": "timeout",
        "stdout": "",
        "stderr": "Execution timed out",
        "exit_code": -1,
        "artifacts": []
    }, indent=2))
    sys.exit(1)

except Exception as e:
    print(json.dumps({
        "status": "failure",
        "stdout": "",
        "stderr": str(e),
        "exit_code": -1,
        "artifacts": []
    }, indent=2))
    sys.exit(1)
```

---

## 🖥️ CLI Integration Script

The CLI wrapper script integrates `reasoning_node.py` and `executor_node.py` to provide an interactive command-line experience.

```bash
#!/bin/bash

# agentic_ai.sh - Main CLI entry point

echo "🐉 Kali GPT Agent Console"
echo "─────────────────────────────"

while true; do
  read -p "> " user_input
  if [[ "$user_input" == "exit" ]]; then break; fi

  # Generate plan via reasoning_node.py
  echo "[🧠 Reasoning & Planning...]"
  json_output=$(python3 reasoning_node.py "$user_input")

  echo "$json_output" | jq -r '"[REASONING] " + .reasoning'
  echo "$json_output" | jq -r '"[TOOL] " + .tool'
  echo "$json_output" | jq -r '"[COMMAND] " + .command'

  # Execute plan using executor_node.py
  echo "[⚙️ EXECUTING TOOL INSIDE KALI...]"
  exec_output=$(ssh kali@192.168.56.10 "python3 /opt/agentic/executor_node.py '$json_output'")

  echo "[📄 RESULTS]"
  echo "$exec_output" | jq

done
```

Ensure the remote Kali box has:

* `executor_node.py` installed
* OpenSSH server running
* SSH key-based auth configured from the control host

---

## ✅ Next Steps

1. Implement `reasoning_node.py` to use OpenAI GPT
2. Build executor shell/Python handler inside Kali
3. Create CLI front-end (interactive + batch modes)
4. Define initial tool plugins and test cases
5. Secure communication channel and test integration
