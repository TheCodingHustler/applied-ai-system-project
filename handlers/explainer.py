from claude_client import ClaudeClient
from handlers import tracker

client = ClaudeClient()

SYSTEM = """You are a helpful software engineering mentor.
Explain concepts, task steps, and technical decisions clearly and concisely.
Be practical — focus on what the developer needs to know to move forward.
Keep responses tight: 2–4 short paragraphs max unless a longer answer is genuinely needed."""


def explain(question: str, history: list = None) -> str:
    progress = tracker.get_progress()

    context = ""
    if progress["goal"]:
        context = f"\n\nThe user's current goal: {progress['goal']}\n"
        if progress["steps"]:
            context += "Their task plan:\n"
            for step in progress["steps"]:
                status = "✓" if step["done"] else "○"
                context += f"  {status} Step {step['id']}: {step['title']}\n"

    system = SYSTEM + context
    messages = (history or []) + [{"role": "user", "content": question}]
    response = client.chat(messages, system)
    return client.get_text(response)
