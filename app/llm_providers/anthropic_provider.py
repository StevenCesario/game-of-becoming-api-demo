import anthropic
from typing import Any, Type
from pydantic import BaseModel
from app.llm_providers.base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    """
    An asynchronous provider for Anthropic's Claude API that uses the
    Tool Use feature for reliable, structured JSON output.
    """
    def __init__(self, api_key:str):
        """Initializes the asynchronous Anthropic client."""
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 2048
        self.temperature = 0.3

    async def generate_structured_response(
        self, system_prompt: str, user_prompt: str, response_model: Type[BaseModel]
    ) -> dict[str, Any]:
        """
        Asynchronously generates a structured response from Claude by forcing
        it to use a Pydantic model as a 'tool'.
        """
        tool_definition = {
            "name": response_model.__name__,
            "description": response_model.__doc__ or "A tool for providing structured output based on the user's request.",
            "input_schema": response_model.model_json_schema(),
        }

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[tool_definition],
                tool_choice={"type": "tool", "name": response_model.__name__},
            )

            # Find the tool_use block in the response content
            tool_use_block = next((block for block in message.content if block.type == "tool_use"), None)

            if tool_use_block:
                # The 'input' field of the tool use block is our structured data
                return tool_use_block.input
            else:
                # This can happen if the AI fails to use the tool as requested
                return {"error": "AI model did not use the requested tool for a structured response."}
        except Exception as e:
            # Catch potential API errors, timeouts etc
            return {"error": f"An exceptoin occured while calling the Anthropic API: {str(e)}"}