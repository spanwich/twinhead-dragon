#!/usr/bin/env python3
"""Reasoning Node for Twinhead Dragon.
Generates structured plans for Kali tools using the OpenAI API.
"""
import os
import sys
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are Kali GPT, an autonomous reasoning agent for offensive security.
Given a natural-language request, you must produce a structured JSON plan
for a Kali Linux tool.

Respond ONLY with JSON, using this schema:
{
  "reasoning": "...",
  "tool": "...",
  "command": "...",
  "next": "..."
}
Only respond with JSON. Do not include explanations outside the JSON object.
"""

def generate_plan(user_input: str) -> dict:
    """Generate a plan using the OpenAI API."""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        temperature=0.3,
        max_tokens=512,
    )
    output = response["choices"][0]["message"]["content"]
    try:
        return json.loads(output)
    except Exception:
        print("[ERROR] Model response is not valid JSON.")
        print(output)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: reasoning_node.py \"<task description>\"")
        sys.exit(1)
    task_description = sys.argv[1]
    plan = generate_plan(task_description)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[FATAL] {exc}")
        sys.exit(1)
