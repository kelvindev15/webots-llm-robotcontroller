import logging
from common.robot.RobotController import RobotController
from common.robot.llm.RobotAction import RobotAction
import threading
import numpy as np
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionStatus(Enum):
    SUCCESS = 1
    FAILURE = 2
    OBSTACLE_DETECTED = 3
    
@dataclass
class ActionResult:
    status: ActionStatus
    message: str = ""

class ActionAdapter:

    def __init__(self, robotController: RobotController):
        self.robot = robotController
        self.actionMap = {
            "FRONT": self.robot.goFront,
            "BACK": self.robot.goBack,
            "ROTATE_LEFT": self.robot.rotateLeft,
            "ROTATE_RIGHT": self.robot.rotateRight,
        }

    async def execute(self, action: RobotAction) -> ActionResult:
        command = action.command
        parameter = action.parameter
        if command in self.actionMap:
            task = threading.Thread(target=self.actionMap[command], args=(parameter,))
            task.start()
            task.join()
            self.robot.stop()
            return ActionResult(status=ActionStatus.SUCCESS, message=f"Executed {command} with parameter {parameter}")
        else:
            print("ActionAdapter: Unknown command", command)
            return ActionResult(status=ActionStatus.FAILURE, message="Unknown command")
        
    def checkSafety(self, action: RobotAction, lidar: list[float] = []) -> bool:
        command = action.command
        parameter = action.parameter
        if command == "FRONT" and np.min(lidar) < parameter:
            return False
        return True    