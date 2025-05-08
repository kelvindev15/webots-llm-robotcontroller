from controllers.webots.adapters.motor import WBMotor
from controller import Supervisor
from enum import Enum

MAX_SPEED = 6.28

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
    def __init__(self, supervisor: Supervisor, timeStep=32):
        self.supervisor: Supervisor = supervisor
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
    
    def __getWheelMotor(self, position: WheelPosition, side: str, timeStep: int):
        return WBMotor(
            self.supervisor.getDevice(f"{position.value}_caster_{side}_wheel_joint"),
            self.supervisor.getDevice(f"{position.value}_caster_{side}_wheel_joint_sensor"),
            timeStep
        )
    
    def __getCasterMotor(self, position: WheelPosition, timeStep: int):
        return WBMotor(
            self.supervisor.getDevice(f"{position.value}_caster_rotation_joint"),
            self.supervisor.getDevice(f"{position.value}_caster_rotation_joint_sensor"),
            timeStep
        )
    
    def __getWheel(self, position: WheelPosition, timeStep: int):
        return PR2Wheel(
            self.__getWheelMotor(position, "l", timeStep),
            self.__getWheelMotor(position, "r", timeStep)
        )
    
    def __getCasterWheel(self, position: WheelPosition, timeStep: int):
        return PR2CasterWheel(
            self.__getWheel(position, timeStep),
            self.__getCasterMotor(position, timeStep)
        )
    
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
