from controller import Supervisor
from common.robot import WheelDevice
from common.robot.RobotController import RobotController

class KheperaController(RobotController):
    def __init__(self, supervisor: Supervisor, timeStep=32, max_speed=6.28):
        super().__init__(max_speed)
        self.supervisor = supervisor
        self.camera = self.supervisor.getDevice("camera")
        self.camera.enable(timeStep)
        self.leftWheel = WheelDevice(
            self.supervisor.getDevice("left wheel motor"))
        self.rightWheel = WheelDevice(
            self.supervisor.getDevice("right wheel motor"))

    def moveForward(self, speed: float = 1.0):
        self.leftWheel.setVelocity(speed * self.max_speed)
        self.rightWheel.setVelocity(speed * self.max_speed)

    def moveBackward(self, speed: float = 1.0):
        self.leftWheel.setVelocity(-speed * self.max_speed)
        self.rightWheel.setVelocity(-speed * self.max_speed)

    def turnLeft(self, speed: float = 1.0):
        self.leftWheel.setVelocity(-speed * self.max_speed)
        self.rightWheel.setVelocity(speed * self.max_speed)

    def turnRight(self, speed: float = 1.0):
        self.leftWheel.setVelocity(speed * self.max_speed)
        self.rightWheel.setVelocity(-speed * self.max_speed)

    def stopMoving(self):
        super().stopMoving()
        self.leftWheel.setVelocity(0)
        self.rightWheel.setVelocity(0)
