import json
import os
import re
from datetime import datetime

TASKS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks.json")

DEFAULT = {
    "goal": None,
    "steps": [],
    "created_at": None,
    "updated_at": None,
}


def load() -> dict:
    if not os.path.exists(TASKS_FILE):
        return DEFAULT.copy()
    with open(TASKS_FILE, "r") as f:
        return json.load(f)


def save(data: dict):
    data["updated_at"] = datetime.now().isoformat()
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def set_goal(goal: str):
    data = load()
    data["goal"] = goal
    data["steps"] = []
    data["created_at"] = datetime.now().isoformat()
    save(data)


def save_steps(steps: list):
    data = load()
    data["steps"] = [{**step, "done": False} for step in steps]
    save(data)


def mark_done(step_id: int) -> bool:
    data = load()
    for step in data["steps"]:
        if step["id"] == step_id:
            step["done"] = True
            save(data)
            return True
    return False


def mark_undone(step_id: int) -> bool:
    data = load()
    for step in data["steps"]:
        if step["id"] == step_id:
            step["done"] = False
            save(data)
            return True
    return False


def get_steps() -> list:
    return load()["steps"]


def get_goal() -> str | None:
    return load()["goal"]


def get_progress() -> dict:
    data = load()
    steps = data["steps"]
    total = len(steps)
    done = sum(1 for s in steps if s["done"])
    return {
        "goal": data["goal"],
        "total": total,
        "done": done,
        "remaining": total - done,
        "percent": int((done / total) * 100) if total > 0 else 0,
        "steps": steps,
    }


def parse_mark_command(content: str) -> dict | None:
    content_lower = content.lower()

    done_match = re.search(
        r"(?:done|complete|finish(?:ed)?)\s+(?:step\s+)?(\d+)", content_lower
    )
    undone_match = re.search(
        r"(?:undo|unmark|reopen)\s+(?:step\s+)?(\d+)", content_lower
    )

    if done_match:
        return {"action": "mark_done", "step_id": int(done_match.group(1))}
    if undone_match:
        return {"action": "mark_undone", "step_id": int(undone_match.group(1))}

    if any(w in content_lower for w in ("reset", "clear", "start over", "new plan")):
        return {"action": "reset"}

    return None


def reset():
    save(DEFAULT.copy())
