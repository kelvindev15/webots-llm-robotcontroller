from common.robot.RobotController import RobotController
from controller import Supervisor
from controllers.webots.adapters.camera import WBCamera

class WBRobotController(RobotController):
    def __init__(self):
        self.supervisor: Supervisor = None
        self.camera: WBCamera = None

    def __checkInitilization(self):
        if not self.supervisor:
            raise Exception("Robot controller not initialized")

    def computeStep(self):
        self.__checkInitilization()
        return self.supervisor.step(32)

    def getPosition(self):
        self.__checkInitilization()
        return self.supervisor.getSelf().getField("translation").getSFVec3f()

    def setPosition(self, position):
        self.__checkInitilization()
        self.supervisor.getSelf().getField("translation").setSFVec3f(position)

    def getRotation(self):
        self.__checkInitilization()
        return self.supervisor.getSelf().getField("rotation").getSFRotation()

    def setRotation(self, rotation):
        self.__checkInitilization()
        self.supervisor.getSelf().getField("rotation").setSFRotation(rotation)

    def getPose(self):
        return {
            "position": self.getPosition(),
            "rotation": self.getRotation()
        }

    def setPose(self, pose):
        self.setPosition(pose["position"])
        self.setRotation(pose["rotation"])
    
    def getCameraImage(self):
        self.__checkInitilization()
        return self.camera.getImage()