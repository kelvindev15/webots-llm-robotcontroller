from controller.motor import Motor
from controller.position_sensor import PositionSensor

class WBMotor():
    def __init__(self, motor: Motor, sensor: PositionSensor, timeStep: int):
        self.motor: Motor = motor
        self.sensor: PositionSensor = sensor
        self.sensor.enable(timeStep)
        self.motor.setPosition(float('inf'))
        self.motor.setVelocity(0)

    def setSpeed(self, speed: float):
        self.motor.setVelocity(speed)

    def setPosition(self, position: float):
        self.motor.setPosition(position)

    def getPosition(self) -> float:
        return self.sensor.getValue()

    def stop(self):
        self.motor.setVelocity(0)
