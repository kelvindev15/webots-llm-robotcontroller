from controllers.webots.adapters.motor import WBMotor
from enum import Enum
import numpy as np
from controllers.webots.pr2.devices import PR2Devices
from simulation.observers import EventManager, EventData, EventType

class PR2Wheel():
    WHEEL_RADIUS = 0.08
    CENTER_TO_WHEEL = 0.318
    MAX_SPEED = 6

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
        self.caster.setSpeed(PR2Wheel.MAX_SPEED)

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
    def __init__(self, devices: PR2Devices, eventManager: EventManager):
        self.locked = False
        self.__TOLERANCE = 0.05
        self.eventManager = eventManager
        self.wheels = {
            WheelPosition.BACK_LEFT: PR2CasterWheel(
                PR2Wheel(devices.BACK_LEFT_LEFT_WHEEL, devices.BACK_LEFT_RIGHT_WHEEL), devices.BACK_LEFT_CASTER
            ),
            WheelPosition.BACK_RIGHT: PR2CasterWheel(
                PR2Wheel(devices.BACK_RIGHT_LEFT_WHEEL, devices.BACK_RIGHT_RIGHT_WHEEL), devices.BACK_RIGHT_CASTER
            ),
            WheelPosition.FRONT_LEFT: PR2CasterWheel(
                PR2Wheel(devices.FRONT_LEFT_LEFT_WHEEL, devices.FRONT_LEFT_RIGHT_WHEEL), devices.FRONT_LEFT_CASTER
            ),
            WheelPosition.FRONT_RIGHT: PR2CasterWheel(
                PR2Wheel(devices.FRONT_RIGHT_LEFT_WHEEL, devices.FRONT_RIGHT_RIGHT_WHEEL), devices.FRONT_RIGHT_CASTER
            )
        }

    def lock(self):
        self.locked = True    
    
    def unlock(self):
        self.locked = False

    def moveForward(self, speed: float = 1.0, distance: float = None):
        self.__setWheelSpeeds(speed, speed, speed, speed)
        if distance != None and not(self.locked):
            self.reach(
                self.wheels[WheelPosition.BACK_LEFT].getPosition,
                targetValue=distance,
                deltaToCurrentValue=lambda delta: delta * PR2Wheel.WHEEL_RADIUS,
            )

    def rotate(self, speed: float = 1.0, angle: float = None):
        self.__setWheelAngles(np.pi/4, -np.pi/4, -np.pi/4, np.pi/4)
        self.__setWheelSpeeds(speed, -speed, speed, -speed)
        if angle != None and not(self.locked):
            self.reach(
                self.wheels[WheelPosition.BACK_LEFT].getPosition,
                targetValue=np.deg2rad(angle),
                deltaToCurrentValue=lambda delta: abs(delta * PR2Wheel.WHEEL_RADIUS / PR2Wheel.CENTER_TO_WHEEL),
            )

    def stop(self):
        self.__setWheelSpeeds(0, 0, 0, 0)
        self.__setWheelAngles(0, 0, 0, 0)        

    def reach(self, getValue, targetValue, deltaToCurrentValue):
        self.lock()
        initialValue = getValue()
        def handler(_: EventData):
            currentValue = getValue()
            delta = abs(currentValue - initialValue)
            actualValue = deltaToCurrentValue(delta)
            if abs(actualValue - targetValue) < self.__TOLERANCE:
                self.unlock()
                self.stop()
                self.eventManager.unsubscribe(handler)   
        self.eventManager.subscribe(EventType.SIMULATION_STEP, handler)
        
    def __setWheelSpeeds(self, bl: float = 0.0, br: float = 0.0, fl: float = 0.0, fr: float = 0.0):
        if not(self.locked):
            self.wheels[WheelPosition.BACK_LEFT].setSpeed(bl * PR2Wheel.MAX_SPEED)
            self.wheels[WheelPosition.BACK_RIGHT].setSpeed(br * PR2Wheel.MAX_SPEED)
            self.wheels[WheelPosition.FRONT_LEFT].setSpeed(fl * PR2Wheel.MAX_SPEED)
            self.wheels[WheelPosition.FRONT_RIGHT].setSpeed(fr * PR2Wheel.MAX_SPEED)

    def __setWheelAngles(self, bl: float = 0.0, br: float = 0.0, fl: float = 0.0, fr: float = 0.0):
        if not(self.locked):    
            self.wheels[WheelPosition.BACK_LEFT].setRotation(bl)
            self.wheels[WheelPosition.BACK_RIGHT].setRotation(br)
            self.wheels[WheelPosition.FRONT_LEFT].setRotation(fl)
            self.wheels[WheelPosition.FRONT_RIGHT].setRotation(fr)         
