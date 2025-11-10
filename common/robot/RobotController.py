from abc import ABC

class RobotController(ABC):
    
    def goFront(self, distance=1.0):
        if not(distance is None) and distance < 0:
            raise ValueError("Distance must be positive")
        pass

    def goBack(self, distance=1.0):
        if not(distance is None) and distance < 0:
            raise ValueError("Distance must be positive")
        pass

    def rotateRight(self, angle=45.0):
        if not(angle is None) and angle < 0:
            raise ValueError("Angle must be positive")
        pass

    def rotateLeft(self, angle=45.0):
        if not(angle is None) and angle < 0:
            raise ValueError("Angle must be positive")
        pass
    
    def stop(self):
        pass

    def getCameraImage(self):
        pass
