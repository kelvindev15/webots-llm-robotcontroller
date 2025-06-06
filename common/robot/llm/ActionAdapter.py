import logging
from common.robot.RobotController import RobotController
from common.robot.llm.RobotAction import RobotAction

logger = logging.getLogger(__name__)

class ActionAdapter:

    def __init__(self, robotController: RobotController):
        self.robot = robotController
        self.actionMap = {
            "FRONT": self.robot.goFront,
            "BACK": self.robot.goBack,
            "ROTATE_LEFT": self.robot.rotateLeft,
            "ROTATE_RIGHT": self.robot.rotateRight,
        }

    def execute(self, action: RobotAction, completionHandler=None) -> bool:
        command = action.command
        parameter = action.parameter
        if command in self.actionMap:
            self.actionMap[command](parameter, completionHandler)
            self.robot.stop()
            return True
        else:
            return False
