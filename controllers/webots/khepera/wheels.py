import numpy as np
from controllers.webots.adapters.motor import WBMotor


class KhepheraWheel:
    WHEEL_RADIUS = 0.021
    CENTER_TO_WHEEL = 0.0527
    MAX_SPEED = 47.6 / 3
    MAX_ACTION_STEP_DURATION = 315

    def __init__(self, motor: WBMotor):
        self.motor = motor

    def setSpeed(self, velocity: float):
        """Set the velocity of the left and right wheels."""
        self.motor.setSpeed(velocity * self.MAX_SPEED)

    def getPosition(self):
        return self.motor.getPosition()

    def reach(self, targetValue, deltaToCurrentValue, completionHandler=None):
        self.motor.reach(targetValue, deltaToCurrentValue, completionHandler)

class KhepheraWheelSystem:
    def __init__(self, left_motor: WBMotor, right_motor: WBMotor):
        self.left_wheel = KhepheraWheel(left_motor)
        self.right_wheel = KhepheraWheel(right_motor)

    def moveForward(self, speed: float = 1.0, distance: float = None, completionHandler=None):
        self.left_wheel.setSpeed(speed)
        self.right_wheel.setSpeed(speed)
        if distance != None:
            self.left_wheel.reach(
                targetValue=distance,
                deltaToCurrentValue=lambda delta: delta * KhepheraWheel.WHEEL_RADIUS,
                completionHandler=completionHandler
            )
        elif completionHandler is not None:
            completionHandler()

    def rotate(self, speed: float = 1.0, angle: float = None, completionHandler=None):
        self.left_wheel.setSpeed(speed)
        self.right_wheel.setSpeed(-speed)
        if angle != None:
            self.left_wheel.reach(
                targetValue=np.deg2rad(angle),
                deltaToCurrentValue=lambda delta: abs(delta * KhepheraWheel.WHEEL_RADIUS / KhepheraWheel.CENTER_TO_WHEEL),
                completionHandler= lambda: (completionHandler() if completionHandler is not None else None, self.stop())
            )
        elif completionHandler is not None:
            completionHandler()

    def stop(self):
        self.left_wheel.setSpeed(0)
        self.right_wheel.setSpeed(0)        

    def reach(self, targetValue, deltaToCurrentValue, completionHandler=None):
        self.left_wheel.reach(targetValue, deltaToCurrentValue, completionHandler)
