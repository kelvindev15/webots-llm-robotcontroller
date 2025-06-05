from dataclasses import dataclass
from common.llm.chats import LLMChat
from common.utils.images import toBase64Image
from common.utils.robot import getDistancesFromLidar, getDistanceDescription
from common.robot.RobotController import RobotController
from common.robot.llm.LLMPlan import LLMPlan
from common.robot.llm.ActionAdapter import ActionAdapter
from common.robot.llm.LLMAdapter import LLMAdapter
from controllers.webots.pr2.PR2Controller import PR2Controller
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
        self.locked = False

    def ask(self, prompt) -> LLMPlan:
        if self.locked:
            logger.debug("Robot is locked, cannot ask.")
            return None
        self.locked = True
        self.llmAdapter.clear()
        def handler(prompt: str):
            action = self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
            if action.command != "COMPLETE":
                view_description = f"""
                Here is the current view of the robot.

                {getDistanceDescription(getDistancesFromLidar(self.robot.getFrontLidarImage(), 90))}
                """.strip()
                self.actionAdapter.execute(action, lambda: handler(view_description if isinstance(self.robot, PR2Controller) else "Current view:"))
            else:
                self.locked = False
                logger.debug("Plan completed")    
        handler(prompt)
    