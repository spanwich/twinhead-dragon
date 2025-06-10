# Twinhead Dragon (Temporary Name)

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

---

## ✅ Next Steps

1. Finalize CLI interface behavior
2. Choose executor bridge (`ssh`, `docker`, etc.)
3. Define initial tool command schemas
4. Implement planner with OpenAI integration
5. Build result parser and feedback loop
