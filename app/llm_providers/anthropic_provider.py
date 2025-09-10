import anthropic
from typing import Dict, Any
from pydantic import BaseModel
from .base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key) # Now using AsyncAnthropic!
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 2048
        self.temperature = 0.3

    # This method now becomes an async function
    async def generate_structured_response(
        self, system_prompt: str, user_prompt: str, response_model: BaseModel
    ) -> Dict[str, Any]:
        tool_definition = {
            "name": response_model.__name__,
            "description": response_model.__doc__ or "Tool for structured output.",
            "input_schema": response_model.model_json_schema(),
        }
        try:
            # The API call is now "awaited"
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool_definition],
                tool_choice={"type": "tool", "name": response_model.__name__},
            )
            tool_use_block = next((b for b in message.content if b.type == "tool_use"), None)
            if tool_use_block:
                return tool_use_block.input
            else:
                return {"error": "AI did not use the requested tool."}
        except Exception as e:
            return {"error": str(e)}
        
    # NEW: Implementation for our new text generation method
    async def generate_text_response(
            self, system_prompt: str, user_prompt: str
    ) -> str:
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # The response is simpler, we just get the text from the first content block
            return message.content[0].text
        except Exception as e:
            # Return to a simple fallback if the AI call fails
            return "Let's move on to the next step"