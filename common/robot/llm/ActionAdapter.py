import logging
from common.robot.RobotController import RobotController
from common.robot.llm.RobotAction import RobotAction
import threading

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

    async def execute(self, action: RobotAction, completionHandler=None) -> bool:
        command = action.command
        parameter = action.parameter
        if command in self.actionMap:
            task = threading.Thread(target=self.actionMap[command], args=(parameter,))
            task.start()
            task.join()
            self.robot.stop()
            return True
        else:
            print("ActionAdapter: Unknown command", command)
            return False
