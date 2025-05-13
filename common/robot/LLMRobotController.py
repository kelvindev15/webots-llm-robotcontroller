from dataclasses import dataclass
from common.llm.chats import LLMChat
from common.utils.images import toBase64Image
from common.robot.RobotController import RobotController
from common.robot.llm.RobotAction import RobotAction
from common.robot.llm.LLMPlan import LLMPlan
from common.robot.llm.ActionAdapter import ActionAdapter
from common.robot.llm.LLMAdapter import LLMAdapter
import logging
import sys

logger = logging.getLogger(__name__)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat):
        self.robot = robotController
        self.chat = chat
        self.llmAdapter = LLMAdapter(chat)
        self.actionAdapter = ActionAdapter(robotController)

    def ask(self, prompt) -> LLMPlan:
        self.llmAdapter.clear()
        action = self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
        plan = LLMPlan(prompt, [action])
        while action.command != "COMPLETE":
            action = self.llmAdapter.iterate("Current view:", toBase64Image(self.robot.getCameraImage()))
            plan = LLMPlan(plan.goal, plan.actions + [action])
            self.actionAdapter.execute(action)
        return plan
    