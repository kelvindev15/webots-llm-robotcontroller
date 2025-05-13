from controllers.webots.adapters.motor import WBMotor
from controller import Supervisor
from enum import Enum
import numpy as np
from controller.constants import constant 

MAX_SPEED = 6.28
TOLERANCE = 0.05
WHEEL_RADIUS = 0.08
CENTER_TO_WHEEL = 0.318

class PR2Wheel():
    def __init__(self, l_wheel: WBMotor, r_wheel: WBMotor):
        self.wheels = {
            "L": l_wheel,
            "R": r_wheel
        }

    def setSpeed(self, velocity: float):
        for _, w in self.wheels.items():
            w.setSpeed(velocity)
    
    def getPosition(self):
        return self.wheels["L"].getPosition()
    
class PR2CasterWheel():
    def __init__(self, wheel: PR2Wheel, caster: WBMotor):
        self.wheel = wheel
        self.caster = caster
        self.caster.setPosition(0)
        self.caster.setSpeed(MAX_SPEED)

    def setSpeed(self, velocity: float):
        self.wheel.setSpeed(velocity)
    
    def getPosition(self):
        return self.wheel.getPosition()

    def setRotation(self, angle: float):
        return self.caster.setPosition(angle)
    
class WheelPosition(Enum):
    FRONT_LEFT = "fl"
    FRONT_RIGHT = "fr"
    BACK_LEFT = "bl"
    BACK_RIGHT = "br" 

class PR2WheelSystem:
    def __init__(self, supervisor: Supervisor, stepFunction, timeStep=32):
        self.timeStep = timeStep
        self.supervisor: Supervisor = supervisor
        self.stepFunction = stepFunction
        BACK_LEFT_WHEEL = self.__getCasterWheel(WheelPosition.BACK_LEFT, timeStep)
        BACK_RIGHT_WHEEL = self.__getCasterWheel(WheelPosition.BACK_RIGHT, timeStep)
        FRONT_LEFT_WHEEL = self.__getCasterWheel(WheelPosition.FRONT_LEFT, timeStep)
        FRONT_RIGHT_WHEEL = self.__getCasterWheel(WheelPosition.FRONT_RIGHT, timeStep)
        self.wheels = {
            WheelPosition.BACK_LEFT: BACK_LEFT_WHEEL,
            WheelPosition.BACK_RIGHT: BACK_RIGHT_WHEEL,
            WheelPosition.FRONT_LEFT: FRONT_LEFT_WHEEL,
            WheelPosition.FRONT_RIGHT: FRONT_RIGHT_WHEEL
        }
    
    def __getWheel(self, position: WheelPosition, timeStep: int):
        return PR2Wheel(
            self.__getWheelMotor(position, "l", timeStep),
            self.__getWheelMotor(position, "r", timeStep)
        )
    
    def __getWheelMotor(self, position: WheelPosition, side: str, timeStep: int):
        return WBMotor(
            self.supervisor.getDevice(f"{position.value}_caster_{side}_wheel_joint"),
            self.supervisor.getDevice(f"{position.value}_caster_{side}_wheel_joint_sensor"),
            timeStep
        )
    
    def __getCasterWheel(self, position: WheelPosition, timeStep: int):
        return PR2CasterWheel(
            self.__getWheel(position, timeStep),
            self.__getCasterMotor(position, timeStep)
        )  

    def __getCasterMotor(self, position: WheelPosition, timeStep: int):
        return WBMotor(
            self.supervisor.getDevice(f"{position.value}_caster_rotation_joint"),
            self.supervisor.getDevice(f"{position.value}_caster_rotation_joint_sensor"),
            timeStep
        )

    def moveForward(self, speed: float = 1.0, distance: float = None):
        self.setWheelSpeeds(speed, speed, speed, speed)
        if distance != None:
            self.reach(
                self.wheels[WheelPosition.BACK_LEFT].getPosition,
                targetValue=distance,
                deltaToCurrentValue=lambda delta: delta * WHEEL_RADIUS,
                steppingFunction=self.stepFunction
            )
            self.setWheelSpeeds(0, 0, 0, 0)

    def rotate(self, speed: float = 1.0, angle: float = None):
        self.setWheelAngles(np.pi/4, -np.pi/4, -np.pi/4, np.pi/4)
        self.setWheelSpeeds(speed, -speed, speed, -speed)
        if angle != None:
            self.reach(
                self.wheels[WheelPosition.BACK_LEFT].getPosition,
                targetValue=np.deg2rad(angle),
                deltaToCurrentValue=lambda delta: abs(delta * WHEEL_RADIUS / CENTER_TO_WHEEL),
                steppingFunction=self.stepFunction
            )
            self.setWheelSpeeds(0, 0, 0, 0)
            self.setWheelAngles(0, 0, 0, 0)

    def reach(self, getValue, targetValue, deltaToCurrentValue, steppingFunction):
        initialValue = getValue()
        actualValue = deltaToCurrentValue(0)
        while steppingFunction() != -1 and not(abs(actualValue - targetValue) < TOLERANCE):
            currentValue = getValue()
            delta = abs(currentValue - initialValue)
            actualValue = deltaToCurrentValue(delta)

    def setWheelSpeeds(self, bl: float = 0.0, br: float = 0.0, fl: float = 0.0, fr: float = 0.0):
        self.wheels[WheelPosition.BACK_LEFT].setSpeed(bl * MAX_SPEED)
        self.wheels[WheelPosition.BACK_RIGHT].setSpeed(br * MAX_SPEED)
        self.wheels[WheelPosition.FRONT_LEFT].setSpeed(fl * MAX_SPEED)
        self.wheels[WheelPosition.FRONT_RIGHT].setSpeed(fr * MAX_SPEED)

    def setWheelAngles(self, bl: float = 0.0, br: float = 0.0, fl: float = 0.0, fr: float = 0.0):
        self.wheels[WheelPosition.BACK_LEFT].setRotation(bl)
        self.wheels[WheelPosition.BACK_RIGHT].setRotation(br)
        self.wheels[WheelPosition.FRONT_LEFT].setRotation(fl)
        self.wheels[WheelPosition.FRONT_RIGHT].setRotation(fr)         
