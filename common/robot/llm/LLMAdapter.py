from common.llm.chats import LLMChat
from common.utils.llm import create_message
from common.utils.misc import extractJSON
from common.robot.llm.RobotAction import RobotAction
import logging
import json
from jsonschema import validate

logger = logging.getLogger(__name__)

class LLMAdapter:
    def __init__(self, chat: LLMChat):
        self.chat = chat
        self.responseSchema = {
            "type": "object",
            "properties": {
                "goal": { "type": "string" },
                "scene_description": { "type": "string" },
                "action": {
                    "type": "object",
                    "properties": {
                        "command": { "type": "string" },
                        "parameters": { "type": "number" },
                    },
                    "required": ["command", "parameters"],
                }
            },
            "required": ["goal", "scene_description", "action"],
        }

    def clear(self):
        self.chat.clear_chat()

    def iterate(self, prompt, image) -> RobotAction:
        logger.debug("Prompt: %s", prompt)
        response = self.chat.send_message(create_message(prompt, image))
        logger.debug("Full LLM response: %s", response)
        action = json.loads(extractJSON(response))
        logger.debug("Response JSON extract: %s", action)
        validate(action, self.responseSchema)
        return RobotAction(action["action"]["command"], float(action["action"]["parameters"]))        
