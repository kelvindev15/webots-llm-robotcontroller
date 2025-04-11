from controller import Supervisor
from controller.device import Device
from common.robot.RobotController import CasterDevice, RobotController, WheelDevice
from enum import Enum
import cv2

from common.utils.geometry import angleBetweenVectors, calculateAccuracy, calculateDirectionAccuracy, calculateDistanceAccuracy, normalizeVector, rotateVector


class RobotWheelDevicePair():
    def __init__(self, l_wheel, r_wheel, casterDevice: Device = None):
        self.caster = None if casterDevice is None else CasterDevice(
            casterDevice)
        self.wheels = [WheelDevice(
            l_wheel, None), WheelDevice(r_wheel, None)]

    def setAngle(self, angle: float, rotate: bool = False):
        if self.caster is None:
            raise ValueError("Caster device not set")
        self.caster.setAngle(angle, rotate)

    def rotate(self, angle: float):
        self.setAngle(angle, rotate=True)

    def setVelocity(self, velocity: float):
        for wheel in self.wheels:
            wheel.setVelocity(velocity)


class WheelPosition(Enum):
    FRONT_LEFT = "fl"
    FRONT_RIGHT = "fr"
    BACK_LEFT = "bl"
    BACK_RIGHT = "br"


class PR2Controller(RobotController):

    def __init__(self, supervisor: Supervisor, timeStep=32, max_speed=6.28):
        super().__init__(max_speed)
        self.supervisor = supervisor
        self.camera = self.supervisor.getDevice(
            "wide_stereo_l_stereo_camera_sensor")
        self.camera.enable(timeStep)
        self.wheels = {
            WheelPosition.BACK_LEFT: RobotWheelDevicePair(
                self.supervisor.getDevice("bl_caster_l_wheel_joint"),
                self.supervisor.getDevice("bl_caster_r_wheel_joint"),
                self.supervisor.getDevice("bl_caster_rotation_joint")),
            WheelPosition.BACK_RIGHT: RobotWheelDevicePair(
                self.supervisor.getDevice("br_caster_l_wheel_joint"),
                self.supervisor.getDevice("br_caster_r_wheel_joint"),
                self.supervisor.getDevice("br_caster_rotation_joint")),
            WheelPosition.FRONT_LEFT: RobotWheelDevicePair(
                self.supervisor.getDevice("fl_caster_l_wheel_joint"),
                self.supervisor.getDevice("fl_caster_r_wheel_joint"),
                self.supervisor.getDevice("fl_caster_rotation_joint")),
            WheelPosition.FRONT_RIGHT: RobotWheelDevicePair(
                self.supervisor.getDevice("fr_caster_l_wheel_joint"),
                self.supervisor.getDevice("fr_caster_r_wheel_joint"),
                self.supervisor.getDevice("fr_caster_rotation_joint"))
        }
        self.__initializeArms()

    def __initializeArms(self):
        rightShoulder = self.supervisor.getDevice("r_shoulder_lift_joint")
        rightShoulder.setPosition(1.3963)

        leftShoulder = self.supervisor.getDevice("l_shoulder_lift_joint")
        leftShoulder.setPosition(1.3963)

        rightElbow = self.supervisor.getDevice("r_elbow_flex_joint")
        rightElbow.setPosition(-2.32)

        leftElbow = self.supervisor.getDevice("l_elbow_flex_joint")
        leftElbow.setPosition(-2.32)

    def setWheelVelocity(self, wheelPosition: WheelPosition, velocity: float):
        self.wheels[wheelPosition].setVelocity(velocity * self.max_speed)

    def __setWheelsVelocity(self, positions: list[WheelPosition], velocity):
        for pos in positions:
            self.setWheelVelocity(pos, velocity)

    def setWheelAngle(self, wheelPosition: WheelPosition, angle: float):
        self.wheels[wheelPosition].setAngle(angle)

    def rotateWheelAngle(self, wheelPosition: WheelPosition, angle: float):
        self.wheels[wheelPosition].rotate(angle)

    def __setWheelsAngle(self, positions, angle, rotate=False):
        for pos in positions:
            self.wheels[pos].setAngle(angle, rotate)

    def setFrontWheelsAngle(self, angle):
        self.__setWheelsAngle(
            [WheelPosition.FRONT_LEFT, WheelPosition.FRONT_RIGHT], angle)

    def rotateFrontWheelsAngle(self, angle):
        self.__setWheelsAngle(["fl", "fr"], angle, rotate=True)

    def setBackWheelsAngle(self, angle):
        self.__setWheelsAngle(
            [WheelPosition.BACK_LEFT, WheelPosition.BACK_RIGHT], angle)

    def rotateBackWheelsAngle(self, angle):
        self.__setWheelsAngle(["bl", "br"], angle, rotate=True)

    def __setWheelAnglesToTurn(self):
        self.setWheelAngle(WheelPosition.FRONT_LEFT, -0.79)
        self.setWheelAngle(WheelPosition.FRONT_RIGHT, 0.79)
        self.setWheelAngle(WheelPosition.BACK_LEFT, 0.79)
        self.setWheelAngle(WheelPosition.BACK_RIGHT, -0.79)

    def moveForward(self, speed=1.0):
        super().moveForward()
        self.__setWheelsVelocity(list(WheelPosition), speed)

    def moveBackward(self, speed=1.0):
        super().moveBackward()
        self.__setWheelsVelocity(list(WheelPosition), -speed)

    def stopMoving(self):
        super().stopMoving()
        self.__setWheelsVelocity(list(WheelPosition), 0)
        self.restoreWheelAngles()

    def turnRight(self, speed=1.0):
        super().turnRight()
        self.__setWheelAnglesToTurn()
        self.__setWheelsVelocity(
            [WheelPosition.FRONT_LEFT, WheelPosition.BACK_LEFT], speed)
        self.__setWheelsVelocity(
            [WheelPosition.FRONT_RIGHT, WheelPosition.BACK_RIGHT], -speed)

    def turnLeft(self, speed=1.0):
        super().turnLeft()
        self.__setWheelAnglesToTurn()
        self.__setWheelsVelocity(
            [WheelPosition.FRONT_LEFT, WheelPosition.BACK_LEFT], -speed)
        self.__setWheelsVelocity(
            [WheelPosition.FRONT_RIGHT, WheelPosition.BACK_RIGHT], speed)

    def restoreWheelAngles(self):
        self.__setWheelsAngle(list(WheelPosition), 0)

    def getDistanceFrom(self, x, y):
        position = self.getPosition()
        return ((position[0] - x)**2 + (position[2] - y)**2)**0.5

    def getDirectionVector(self):
        return rotateVector([1, 0], self.getRotation()[3])

    def calculateTargetReachingAccuracy(self, x, y):
        robot_direction = self.getDirectionVector()
        object_direction = [x - self.getPosition()[0], y -
                            self.getPosition()[2]]
        object_direction = normalizeVector(object_direction)
        angle = angleBetweenVectors(robot_direction, object_direction)
        distance = self.getDistanceFrom(x, y)
        print(angle)
        return {
            "distanceAccuracy": calculateDistanceAccuracy(distance),
            "directionAccuracy": calculateDirectionAccuracy(angle),
            "accuracy": calculateAccuracy(distance, angleBetweenVectors(robot_direction, [x, y]))
        }
