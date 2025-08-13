from anthropic import AsyncAnthropic
#from app.models import DailyReflectionResult  # placeholder for the future
from pydantic import BaseModel
from app.llm_providers.base import BaseLLMProvider
import os
import json

class AnthropicProvider(BaseLLMProvider):
    """
    Uses Anthropic's Claude (messages API) to generate structured JSON
    that conforms to any Pydantic model we pass in.
    """

    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel]
    ) -> dict[str, object]:
        """
        Returns a validated dict via Pydantic.
        Example usage:
            cls = AnthropicProvider()
            data = await cls.generate_structured_response(
                system="Return valid JSON …",
                user="Generate a reflection for today",
                response_model=ReflectionResult
            )
            # data is already a Python dict validated with ReflectionResult
        """
        resp = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt.strip(),
            messages=[{"role": "user", "content": user_prompt.strip()}],
            temperature=0.3,
            timeout=30,
        )
        text = resp.content[0].text.strip()
        try:
            # Attempt JSON parse immediately
            raw = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: wrap in a simple extra layer
            raw = json.loads(self._fallback_json_extract(text))

        # Let pydantic run validation
        return response_model(**raw).model_dump()

    @staticmethod
    def _fallback_json_extract(text: str) -> str: # Defensive cleaning logic to protect against malformed Claude replies
        """
        Trim markdown fences or trailing explanation text so
        JSON.loads always gets clean JSON before pydantic runs validation.
        """
        text = text.removeprefix("```json").removesuffix("```").strip()
        # Naive lock-in on first `{ ... }` pair
        if text.startswith("{"):
            brace_end = text.rfind("}", 0) + 1
            return text[:brace_end]
        return text
