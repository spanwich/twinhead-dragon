#!/usr/bin/env python3
"""Executor Node for Twinhead Dragon.
Executes planned commands in a controlled environment.
"""
import json
import subprocess
import sys
import os
import datetime

LOG_DIR = "/var/log/agentic_ai"
os.makedirs(LOG_DIR, exist_ok=True)


def load_task(raw: str) -> dict:
    """Load JSON from a string or file path."""
    if os.path.exists(raw):
        with open(raw) as f:
            return json.load(f)
    return json.loads(raw)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: executor_node.py '<json_file_or_raw_input>'")
        sys.exit(1)

    task = load_task(sys.argv[1])
    tool = task.get("tool")
    command = task.get("command")
    timeout = int(task.get("timeout", 60))

    if not tool or not command:
        raise ValueError("Missing required fields: 'tool' or 'command'")

    print(f"[INFO] Running tool: {tool}")
    print(f"[CMD] {command}")

    try:
        result = subprocess.run(command, shell=True, capture_output=True,
                                timeout=timeout, text=True)
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "status": "timeout",
            "stdout": "",
            "stderr": "Execution timed out",
            "exit_code": -1,
            "artifacts": []
        }, indent=2))
        sys.exit(1)

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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "status": "failure",
            "stdout": "",
            "stderr": str(exc),
            "exit_code": -1,
            "artifacts": []
        }, indent=2))
        sys.exit(1)
