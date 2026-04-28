from claude_client import ClaudeClient
from handlers import planner, debugger, explainer, tracker

client = ClaudeClient()

MAX_HISTORY = 20  # keep last 10 conversation turns

INTENT_SYSTEM = """You are an intent classifier for an AI task-planning assistant.
Classify the user's message into exactly one intent and extract the core content.
Use the classify_intent tool to return your response.

Intents:
- plan:    user wants to plan a new goal or project
- debug:   user wants to debug code, an error message, or a bug
- explain: user wants an explanation of something (a step, a concept, a decision)
- track:   user wants to see progress, mark a step done/undone, or reset the plan
- unknown: none of the above"""

INTENT_TOOL = {
    "name": "classify_intent",
    "description": "Classify the user's intent and extract the main content",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["plan", "debug", "explain", "track", "unknown"],
            },
            "extracted_content": {
                "type": "string",
                "description": "The main content from the message: the goal, code, question, or command",
            },
        },
        "required": ["intent", "extracted_content"],
    },
}


class Agent:
    def __init__(self):
        self.history: list = []

    def _detect_intent(self, user_input: str) -> dict:
        messages = [{"role": "user", "content": user_input}]
        response = client.chat(messages, INTENT_SYSTEM, tools=[INTENT_TOOL])
        result = client.get_tool_input(response)
        return result or {"intent": "unknown", "extracted_content": user_input}

    def _trim_history(self):
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]

    def run(self, user_input: str) -> dict:
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()

        intent_result = self._detect_intent(user_input)
        intent = intent_result["intent"]
        content = intent_result["extracted_content"]

        try:
            if intent == "plan":
                steps = planner.plan(content)
                result = {"type": "plan", "steps": steps, "goal": content}

            elif intent == "debug":
                diagnosis = debugger.debug(content, self.history[:-1])
                result = {"type": "debug", "diagnosis": diagnosis}

            elif intent == "explain":
                text = explainer.explain(content, self.history[:-1])
                result = {"type": "explain", "text": text}

            elif intent == "track":
                result = self._handle_track(content)

            else:
                # treat unknown as a question
                text = explainer.explain(user_input, self.history[:-1])
                result = {"type": "explain", "text": text}

        except Exception as e:
            result = {"type": "error", "message": str(e)}

        self.history.append({"role": "assistant", "content": str(result)})
        return result

    def _handle_track(self, content: str) -> dict:
        command = tracker.parse_mark_command(content)

        if command is None:
            progress = tracker.get_progress()
            return {"type": "track", "action": "progress", "progress": progress}

        action = command["action"]

        if action == "reset":
            tracker.reset()
            return {"type": "track", "action": "reset"}

        step_id = command["step_id"]
        if action == "mark_done":
            success = tracker.mark_done(step_id)
        else:
            success = tracker.mark_undone(step_id)

        progress = tracker.get_progress()
        return {
            "type": "track",
            "action": action,
            "step_id": step_id,
            "success": success,
            "progress": progress,
        }
