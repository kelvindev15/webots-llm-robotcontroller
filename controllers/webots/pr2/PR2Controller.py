from controllers.webots.pr2.wheels import PR2WheelSystem
from controllers.webots.WBRobotController import WBRobotController
from simulation.observers import EventManager, EventType, EventData
from controllers.webots.pr2.devices import PR2Devices
import numpy as np


def unlockAndHandle(unlocker, handler):
    unlocker()
    if handler is not None:
        handler()
        
class PR2Controller(WBRobotController):

    def __init__(self, devices: PR2Devices, eventManager: EventManager=None):
        super().__init__()
        self.devices = devices
        self.camera = devices.CAMERA
        self.lidar = devices.BASE_LASER
        self.tiltLidar = devices.TILT_LIDAR
        self.wheelSystem = PR2WheelSystem(devices, eventManager)
        self.__initializeArms()
        self.eventManager = eventManager
        self.devices.TILT_LIDAR.setPointCloudEnabled(False)
        eventManager.subscribe(EventType.SIMULATION_STEP, self.__onSimulationStep)    
    
    def __onSimulationStep(self, _: EventData):
        self.devices.HEAD_PAN_JOINT.setPositionByPercentage(0.5)

    def __initializeArms(self):
        self.devices.LEFT_SHOULDER_LIFT.setToMaxPosition()
        self.devices.RIGHT_SHOULDER_LIFT.setToMaxPosition()
        
        self.devices.LEFT_ELBOW_FLEX.setToMinPosition()
        self.devices.RIGHT_ELBOW_FLEX.setToMinPosition()

    def goFront(self, distance=1.0):
        super().goFront(distance)
        res = self.wheelSystem.moveForward(1.0, distance)
        if res is not None:
            res.result()
            self.stop()
       
    def goBack(self, distance=1.0):
        super().goBack(distance)
        res = self.wheelSystem.moveForward(-1.0, distance)
        if res is not None:
            res.result()
            self.stop()

    def rotateLeft(self, angle=1.0):
        super().rotateLeft(angle)
        res = self.wheelSystem.rotate(speed=-1.0, angle=angle)
        if angle is not None:
            res.result()
            self.stop()

    def rotateRight(self, angle=1.0):
        super().rotateRight(angle)
        res = self.wheelSystem.rotate(speed=1.0, angle=angle)
        if angle is not None:
            res.result()
            self.stop()

    def stop(self):
        super().stop()
        self.wheelSystem.stop()

    def getDepthImage(self):
        samples = np.linspace(0.0, 1.0, 300)
        end = len(samples)
        def handler(index):
            if index < end:
                self.tiltLidar.setPositionByPercentage(samples[index+1], onComplete=lambda: handler(index + 1))
        self.tiltLidar.setPositionByPercentage(samples[0], onComplete=lambda: handler(0))

    def moveTiltLidarUp(self, onComplete=None):
        self.tiltLidar.moveUp(onComplete)

    def moveTiltLidarDown(self, onComplete=None):
        self.tiltLidar.moveDown(onComplete)

    def getTiltLidarPositionPercent(self):
        return self.tiltLidar.getPositionPercent()

    def stopTiltLidar(self):
        self.tiltLidar.stop()

    def getFullLidarImage(self):
        return self.lidar.getImage()
        
    def getFrontLidarImage(self):
        return self.lidar.getPoints(90)
    
    def getLeftLidarImage(self):
        return self.lidar.getPoints(85, -90)
    
    def getRightLidarImage(self):
        return self.lidar.getPoints(85, 90)
    
    def getLidarImage(self, fov: int, rotation_degrees: int):
        return self.lidar.getPoints(fov, rotation_degrees)
    