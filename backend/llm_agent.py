import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def diagnose(error: dict, code_snippet: str, file_history: str = "") -> dict:
    """
    Given a structured error, its code context, and optional git history, ask the LLM to diagnose it.
    Returns: {root_cause, suggested_fix, confidence}
    """
    history_section = f"\n{file_history}\n" if file_history else ""

    prompt = f"""You are a senior software engineer debugging a codebase.

ERROR TYPE: {error['error_type']}
ERROR MESSAGE: {error['message']}
LOCATION: {error['file']}, line {error['line_number']}, in function {error.get('function', 'unknown')}

STACK TRACE:
{error['raw_trace']}

RELEVANT CODE (>> marks the exact line that raised the error):
{code_snippet}
{history_section}
Diagnose the root cause of this error and suggest a fix. If recent commits are shown above and seem relevant to the error, mention that connection in your root cause explanation.

Respond ONLY with valid JSON, no other text, in this exact format:
{{"root_cause": "one or two sentence explanation", "suggested_fix": "concrete fix suggestion, can include a short code snippet", "confidence": "high, medium, or low"}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "root_cause": "Could not parse LLM response",
            "suggested_fix": text,
            "confidence": "low"
        }

if __name__ == "__main__":
    sample_error = {
        "error_type": "ZeroDivisionError",
        "message": "division by zero",
        "file": "app.py",
        "line_number": 42,
        "function": "process_data",
        "raw_trace": "Traceback (most recent call last):\n  File \"app.py\", line 55, in main\n    process_data(items)\n  File \"app.py\", line 42, in process_data\n    result = 10 / count\nZeroDivisionError: division by zero"
    }
    sample_code = """  37:     def process_data(items):
  38:         count = 0
  39:         for item in items:
  40:             if item.valid:
  41:                 count += 1
>> 42:         result = 10 / count
  43:         return result"""

    result = diagnose(sample_error, sample_code)
    print(json.dumps(result, indent=2))