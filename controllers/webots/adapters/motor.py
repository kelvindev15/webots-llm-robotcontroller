from controller.motor import Motor
from controller.position_sensor import PositionSensor
from controller.constants import constant

class WBMotor():
    def __init__(self, motor: Motor, timeStep: int, minPosition: float = -float('inf'), maxPosition: float = float('inf')):
        self.motor: Motor = motor
        self.sensor: PositionSensor = self.motor.position_sensor
        self.minPosition = minPosition
        self.maxPosition = maxPosition
        self.sensor.enable(timeStep)
        self.motor.setPosition(float('inf'))
        self.motor.setVelocity(0)

    def setSpeed(self, speed: float):
        self.motor.setVelocity(speed)

    def getSpeed(self) -> float:
        return self.motor.getVelocity()    

    def setPosition(self, position: float):
        self.motor.setPosition(position)

    def setPositionByPercentage(self, percent: float):
        position = self.minPosition + (self.maxPosition - self.minPosition) * percent
        self.setPosition(position)

    def getPosition(self) -> float:
        return self.sensor.getValue()

    def stop(self):
        self.motor.setVelocity(0)

    def toMinPosition(self):
        self.setPosition(self.minPosition)

    def toMaxPosition(self):    
        self.setPosition(self.maxPosition)    

    @property
    def isRotational(self) -> bool:
        return self.motor.getType() == constant("ROTATIONAL")    
