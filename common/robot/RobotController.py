from abc import ABC
from controller import Supervisor
from controller.device import Device
from common.utils.images import extractColorChannel
import cv2


class CasterDevice():
    def __init__(self, casterDevice: Device, initialAngle: float = 0):
        self.device = casterDevice
        self.angle = initialAngle
        self.device.setPosition(initialAngle)

    def setAngle(self, angle: float, rotate: bool = False):
        self.angle = angle
        self.device.setPosition(angle + (self.angle if rotate else 0))

    def rotate(self, angle: float):
        self.setAngle(angle, rotate=True)


class WheelDevice():
    def __init__(self, wheelDevice: Device, casterDevice: Device = None):
        self.wheel = wheelDevice
        self.caster = None if casterDevice is None else CasterDevice(
            casterDevice)
        self.wheel.setPosition(float('inf'))
        self.wheel.setVelocity(0.0)

    def setVelocity(self, velocity: float):
        self.wheel.setVelocity(velocity)

    def setAngle(self, angle: float, rotate: bool = False):
        if self.caster is None:
            raise ValueError("Caster device not set")
        self.caster.setAngle(angle, rotate)

    def rotate(self, angle: float):
        self.setAngle(angle, rotate=True)


class RobotController(ABC):
    def __init__(self, max_speed=1.0):
        self.supervisor: Supervisor = None
        self.camera: Device = None
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
        # Get image dimensions
        image_data = self.camera.getImage()
        image_width = self.camera.getWidth()
        image_height = self.camera.getHeight()

        # Extract RGB channels
        red_channel = extractColorChannel(
            image_data, self.camera.imageGetRed, image_width, image_height)
        green_channel = extractColorChannel(
            image_data, self.camera.imageGetGreen, image_width, image_height)
        blue_channel = extractColorChannel(
            image_data, self.camera.imageGetBlue, image_width, image_height)

        # Combine channels into final image
        output_image = cv2.merge([blue_channel, green_channel, red_channel])
        return output_image

    def getDirectionVector(self):
        pass

    def getDistanceFrom(self, x, y):
        pass

    def calculateTargetReachingAccuracy(self, x, y):
        pass
