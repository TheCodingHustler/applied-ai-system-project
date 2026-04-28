from claude_client import ClaudeClient
from handlers import tracker

client = ClaudeClient()

SYSTEM = """You are an expert software engineering task planner.
When given a goal, break it into 5–10 clear, actionable steps a developer can follow in order.
Each step must be specific — no vague steps like "set up project". Instead write "Create a Python
virtual environment and install dependencies: flask, sqlalchemy, pytest".
Always use the create_task_plan tool to return your response."""

TOOL = {
    "name": "create_task_plan",
    "description": "Create a structured step-by-step development plan for the given goal",
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "estimated_time": {"type": "string"},
                    },
                    "required": ["id", "title", "description", "estimated_time"],
                },
            }
        },
        "required": ["steps"],
    },
}


def plan(goal: str) -> list:
    tracker.set_goal(goal)
    messages = [{"role": "user", "content": f"Goal: {goal}"}]
    response = client.chat(messages, SYSTEM, tools=[TOOL])
    result = client.get_tool_input(response)
    if result and "steps" in result:
        tracker.save_steps(result["steps"])
        return result["steps"]
    return []
