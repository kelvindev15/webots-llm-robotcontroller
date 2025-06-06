from controller.motor import Motor
from controller.position_sensor import PositionSensor
from controller.constants import constant
from simulation.observers import EventManager, EventData, EventType
from typing import Callable

MAX_ACTION_STEP_DURATION = 315

class WBMotor():
    def __init__(self, motor: Motor, timeStep: int, eventManager: EventManager):
        self.motor: Motor = motor
        self.eventManager: EventManager = eventManager
        self.sensor: PositionSensor = self.motor.position_sensor
        self.minPosition = self.motor.min_position
        self.maxPosition = self.motor.max_position
        self.maxVelocity = self.motor.max_velocity
        self.sensor.enable(timeStep)
        self.motor.setPosition(float('inf'))
        self.motor.setVelocity(0)

    def setSpeed(self, speed: float):
        self.motor.setVelocity(speed)

    def getSpeed(self) -> float:
        return self.motor.getVelocity()    

    def setPosition(self, position: float):
        self.motor.setPosition(position)

    def getPositionPercent(self) -> float:
        position_range = self.maxPosition - self.minPosition
        return (self.getPosition() - self.minPosition) / (position_range if position_range != 0 else 1.0)

    def setPositionByPercentage(self, percent: float, onComplete: Callable[[None], None] = None):
        position = self.minPosition + (self.maxPosition - self.minPosition) * percent
        self.setPosition(position)
        self.setSpeed(self.maxVelocity)
        def handler(_: EventData):
            if self.__fuzzyEquals(self.getPositionPercent(), percent):
                self.eventManager.unsubscribe(abort_handler)
                onComplete()
                self.eventManager.unsubscribe(handler)
        if onComplete is not None:
            self.eventManager.subscribe(EventType.SIMULATION_STEP, handler)
            def abort_handler(_: EventData):
                self.eventManager.unsubscribe(handler)
                self.eventManager.unsubscribe(abort_handler)
                self.stop()
                onComplete()
            self.eventManager.subscribe(EventType.ABORT, abort_handler)

    def __fuzzyEquals(self, a: float, b: float, epsilon: float = 0.01) -> bool:
        return abs(a - b) < epsilon

    def getPosition(self) -> float:
        return self.sensor.getValue()

    def stop(self):
        self.motor.setVelocity(0)

    def setToMinPosition(self):
        self.setPositionByPercentage(0.0)

    def setToMaxPosition(self):
        self.setPositionByPercentage(1.0)

    @property
    def isRotational(self) -> bool:
        return self.motor.getType() == constant("ROTATIONAL")   
