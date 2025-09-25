from controllers.webots.WBRobotController import WBRobotController
from controllers.webots.khepera.devices import KhepheraDevices
from controllers.webots.khepera.wheels import KhepheraWheelSystem
from simulation.observers import EventManager


def unlockAndHandle(unlocker, handler):
    unlocker()
    if handler is not None:
        handler()

class KhepheraController(WBRobotController):
    def __init__(self, devices: KhepheraDevices, eventManager: EventManager=None):
        super().__init__()
        self.camera = devices.CAMERA
        self.eventManager = eventManager
        self.wheelSystem = KhepheraWheelSystem(devices.LEFT_WHEEL, devices.RIGHT_WHEEL)
        self.locked = False
        
    def __lock(self):
        self.locked = True

    def __unlock(self):
        self.locked = False

    def goFront(self, distance: float = 1.0, completionHandler=None):
        super().goFront(distance)
        if distance is not None and not self.locked:
            self.__lock()
            self.wheelSystem.moveForward(distance=distance, completionHandler=lambda: unlockAndHandle(self.__unlock, completionHandler))
        elif not self.locked:
            self.wheelSystem.moveForward(distance=distance, completionHandler=completionHandler)

    def goBack(self, distance: float = 1.0, completionHandler=None):
        super().goBack(distance)
        if distance is not None and not self.locked:
            self.__lock()
            self.wheelSystem.moveForward(speed=-1.0, distance=distance, completionHandler=lambda: unlockAndHandle(self.__unlock, completionHandler))
        elif not self.locked:
            self.wheelSystem.moveForward(speed=-1.0, distance=distance, completionHandler=completionHandler)

    def rotateLeft(self, angle: float = 1.0, completionHandler=None):
        super().rotateLeft(angle)
        if angle is not None and not self.locked:
            self.__lock()
            self.wheelSystem.rotate(speed=-1.0, angle=angle, completionHandler=lambda: (unlockAndHandle(self.__unlock, completionHandler), self.stop()))
        else:
            self.wheelSystem.rotate(speed=-1.0, angle=angle, completionHandler=completionHandler)

    def rotateRight(self, angle: float = 1.0, completionHandler=None):
        super().rotateRight(angle)
        if angle is not None and not self.locked:
            self.__lock()
            self.wheelSystem.rotate(angle=angle, completionHandler=lambda: (unlockAndHandle(self.__unlock, completionHandler), self.stop()))
        else:
            self.wheelSystem.rotate(angle=angle, completionHandler=completionHandler)

    def stop(self):
        if not self.locked:
            super().stop()
            self.wheelSystem.stop()
