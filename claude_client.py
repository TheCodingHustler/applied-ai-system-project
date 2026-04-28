import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-6"

    def chat(self, messages: list, system: str, tools: list = None) -> object:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "system": [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = {"type": "any"}

        return self.client.messages.create(**kwargs)

    def get_text(self, response) -> str:
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    def get_tool_input(self, response) -> dict | None:
        for block in response.content:
            if block.type == "tool_use":
                return block.input
        return None
