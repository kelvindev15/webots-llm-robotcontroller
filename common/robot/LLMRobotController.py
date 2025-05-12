from dataclasses import dataclass
import os

from common.llm.chats import LLMChat
from common.utils.experiments import get_next_experiment_number, getExperimentFolderById
from common.utils.images import saveImage, toBase64Image
from common.utils.llm import create_message
from common.robot.RobotController import RobotController
import json
from common.utils.misc import extractJSON
from jsonschema import validate
from typing import List

@dataclass
class RobotAction:
    command: str
    parameter: float

@dataclass
class LLMPlan():
    goal: str
    actions: List[RobotAction]

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
        response = self.chat.send_message(create_message(prompt, image))
        action = json.loads(extractJSON(response))
        validate(action, self.responseSchema)
        return RobotAction(action["action"]["command"], float(action["action"]["parameters"]))        

class ActionAdapter:
    
    def __init__(self, robotController: RobotController):
        self.robot = robotController
        self.actionMap = {
            "FRONT": self.robot.moveForward,
            "BACK": self.robot.moveBackward,
            "ROTATE_LEFT": self.robot.rotateLeft,
            "ROTATE_RIGHT": self.robot.rotateRight,
        }

    def execute(self, action: RobotAction):
        command = action.command
        parameter = action.parameter
        if command in self.actionMap:
            self.actionMap[command](parameter)
        elif command == "COMPLETE":
            pass
        else:
            print(f"Unknown command: {command}")

class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat):
        self.robot = robotController
        self.chat = chat
        self.llmAdapter = LLMAdapter(chat)
        self.actionAdapter = ActionAdapter(robotController)

    def ask(self, prompt) -> LLMPlan:
        self.llmAdapter.clear()
        action = self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
        plan = LLMPlan(action.goal, [action])
        while action.command != "COMPLETE":
            action = self.llmAdapter.iterate("Current view:", toBase64Image(self.robot.getCameraImage()))
            plan = LLMPlan(plan.goal, plan.actions + [action])
            self.actionAdapter.execute(action)
        return plan
    