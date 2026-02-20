from common.llm.chats import LLMChat
from common.utils.llm import create_message
from common.utils.misc import extractJSON
from common.robot.llm.RobotAction import Motivation, RobotAction
import logging
import json
from jsonschema import validate
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


@dataclass
class Result(Generic[T]):
    ok: bool
    value: Optional[T] = None
    error: Optional[Exception] = None

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        return cls(ok=True, value=value)

    @classmethod
    def failure(cls, error: Exception) -> "Result[T]":
        return cls(ok=False, error=error)


class InvalidJSON(Exception):
    """Raised when the LLM response doesn't contain valid JSON."""
    def __init__(self, raw: str):
        super().__init__("Invalid JSON from model")
        self.raw = raw


class SchemaValidationError(Exception):
    """Raised when the parsed JSON doesn't match the expected schema."""
    def __init__(self, original: Exception):
        super().__init__("Response did not match schema")
        self.original = original


class LLMAdapter:
    def __init__(self, chat: LLMChat):
        self.chat = chat
        self.responseSchema = {
            "type": "object",
            "properties": {
                "goal": { "type": "string" },
                "scene_description": { "type": "string" },
                "reasoning": { "type": "string" },
                "action": {
                    "type": "object",
                    "properties": {
                        "command": { "type": "string" },
                        "parameters": { "type": "number" },
                    },
                    "required": ["command", "parameters"],
                }
            },
            "required": ["goal", "scene_description", "reasoning", "action"],
        }

    def clear(self):
        self.chat.clear_chat()

    async def iterate(self, prompt, image) -> Result[RobotAction]:
        """Send prompt+image to the chat, extract and validate JSON, and return a Result.

        Success: Result.success(RobotAction)
        Failure: Result.failure(Exception) with one of: InvalidJSON, SchemaValidationError, or other runtime error
        """
        response = await self.chat.send_message(create_message(prompt, image))

        # Attempt to extract JSON string from the model response
        try:
            extracted = extractJSON(response)
            action_obj = json.loads(extracted)
        except Exception as e:
            logger.debug("Failed to extract/parse JSON from response", exc_info=True)
            return Result.failure(InvalidJSON(response))

        # Validate against schema
        try:
            validate(action_obj, self.responseSchema)
        except Exception as e:
            logger.debug("Schema validation failed", exc_info=True)
            return Result.failure(SchemaValidationError(e))

        # Build RobotAction and return
        try:
            cmd = action_obj["action"]["command"]
            params = float(action_obj["action"]["parameters"])
            reasoning = action_obj["reasoning"]
            subgoal = action_obj["goal"]
            scene_description = action_obj["scene_description"]
            motivation = Motivation(subgoal=subgoal, reasoning=reasoning, scene_description=scene_description)
            return Result.success(RobotAction(cmd, params, motivation=motivation))
        except Exception as e:
            logger.debug("Failed to construct RobotAction", exc_info=True)
            return Result.failure(e)

    async def comunicateThatActionIsColliding(self, action: RobotAction) -> Result[RobotAction]:
        return self.iterate(
            f"The given action: {action.command} with parameter {action.parameter} is considered dangerous as it may lead to a collision. Please provide a different action that is safe to execute.", 
            None)