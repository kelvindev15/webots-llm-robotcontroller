from abc import ABC

class RobotController(ABC):
    def __init__(self, max_speed=1.0):
        self.max_speed = max_speed
        
    def moveForward(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def moveBackward(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def rotateRight(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass

    def rotateLeft(self, speed=1.0):
        if speed < 0:
            raise ValueError("Speed must be positive")
        pass
    
    def stop(self):
        pass

    def getCameraImage(self):
        pass
