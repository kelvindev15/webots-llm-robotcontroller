from abc import ABC

class RobotController(ABC):
    def __init__(self, max_speed=1.0):
        self.max_speed = max_speed
        
    def goFront(self, distance=1.0):
        if distance < 0:
            raise ValueError("Distance must be positive")
        pass

    def goBack(self, distance=1.0):
        if distance < 0:
            raise ValueError("Distance must be positive")
        pass

    def rotateRight(self, angle=45.0):
        if angle < 0:
            raise ValueError("Angle must be positive")
        pass

    def rotateLeft(self, angle=45.0):
        if angle < 0:
            raise ValueError("Angle must be positive")
        pass
    
    def stop(self):
        pass

    def getCameraImage(self):
        pass
