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

    def execute(self, action: RobotAction):
        command = action.command
        parameter = action.parameter
        if command in self.actionMap:
            logger.debug("Executing action: %s with parameter: %s", command, parameter)
            self.actionMap[command](parameter)
            self.robot.stop()
        elif command == "COMPLETE":
            logger.debug("Plan completed")
            pass
        else:
            logger.debug("Unknown command: %s", command)

