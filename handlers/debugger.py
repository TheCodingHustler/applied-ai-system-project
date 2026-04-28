from claude_client import ClaudeClient

client = ClaudeClient()

SYSTEM = """You are an expert software debugger and code reviewer.
When given a code snippet, error message, or bug description, analyze it thoroughly.
Always use the diagnose_error tool to return a structured diagnosis.
Be direct and specific. If you can provide a fixed code block, always do so."""

TOOL = {
    "name": "diagnose_error",
    "description": "Diagnose and classify a code error or bug",
    "input_schema": {
        "type": "object",
        "properties": {
            "error_type": {
                "type": "string",
                "enum": ["syntax", "runtime", "logic", "dependency", "config", "unknown"],
                "description": "The category of the error",
            },
            "root_cause": {
                "type": "string",
                "description": "Plain English explanation of exactly why this error occurs",
            },
            "fix_explanation": {
                "type": "string",
                "description": "Step-by-step explanation of how to fix the issue",
            },
            "fixed_code": {
                "type": "string",
                "description": "The corrected code snippet (omit if not applicable)",
            },
            "language": {
                "type": "string",
                "description": "Programming language of the code (e.g. python, javascript, typescript)",
            },
        },
        "required": ["error_type", "root_cause", "fix_explanation"],
    },
}


def debug(code_or_error: str, history: list = None) -> dict:
    messages = (history or []) + [
        {"role": "user", "content": f"Please debug this:\n\n{code_or_error}"}
    ]
    response = client.chat(messages, SYSTEM, tools=[TOOL])
    result = client.get_tool_input(response)
    return result or {
        "error_type": "unknown",
        "root_cause": "Could not analyze the provided input.",
        "fix_explanation": "Please provide more context — paste the full error message or the relevant code block.",
    }
