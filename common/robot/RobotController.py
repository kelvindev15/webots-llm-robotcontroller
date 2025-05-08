from abc import ABC
from controller import Supervisor
from controller.device import Device
import cv2
import numpy as np

class RobotController(ABC):
    def __init__(self, max_speed=1.0):
        self.supervisor: Supervisor = None
        self.max_speed = max_speed

    def __checkInitilization(self):
        if not self.supervisor:
            raise Exception("Robot controller not initialized")

    def moveForward(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def moveBackward(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def turnRight(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def turnLeft(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

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

    def stopMoving(self):
        pass

    def getCameraImage(self):
        pass
    
    def getFullLidarImage(self):
        pass

    def middleClippedLidarImage(self, degrees: float):
        pass

