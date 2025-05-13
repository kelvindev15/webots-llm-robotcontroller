from controller import Supervisor
import numpy as np
from controllers.webots.adapters.lidar import WBLidar
from controllers.webots.adapters.camera import WBCamera
from controllers.webots.pr2.wheels import PR2WheelSystem
from controllers.webots.WBRobotController import WBRobotController
from simulation.observers import EventManager

class PR2Controller(WBRobotController):

    def __init__(self, supervisor: Supervisor, timeStep=32, eventManager: EventManager=None):
        self.wheelSystem = PR2WheelSystem(supervisor, self.doStep, timeStep)
        super().__init__()
        self.supervisor: Supervisor = supervisor
        self.camera = WBCamera(self.supervisor.getDevice("wide_stereo_r_stereo_camera_sensor"), timeStep)
        self.lidar = WBLidar(self.supervisor.getDevice("base_laser"), timeStep)
        self.eventManager = eventManager
        self.__initializeArms()
        
    def __initializeArms(self):
        rightShoulder = self.supervisor.getDevice("r_shoulder_lift_joint")
        rightShoulder.setPosition(1.3963)

        leftShoulder = self.supervisor.getDevice("l_shoulder_lift_joint")
        leftShoulder.setPosition(1.3963)

        rightElbow = self.supervisor.getDevice("r_elbow_flex_joint")
        rightElbow.setPosition(-2.32)

        leftElbow = self.supervisor.getDevice("l_elbow_flex_joint")
        leftElbow.setPosition(-2.32)

    def doStep(self):
        super().doStep()
        if self.eventManager is not None:
            self.eventManager.notify("step", {})

    def goFront(self, distance=1.0):
        super().goFront(distance)
        self.wheelSystem.moveForward(distance=distance)

    def goBack(self, distance=1.0):
        super().goBack(distance)
        self.wheelSystem.moveForward(speed=-1.0, distance=distance)

    def rotateLeft(self, angle=1.0):
        super().rotateLeft(angle)
        self.wheelSystem.rotate(speed=-1.0, angle=angle)

    def rotateRight(self, angle=1.0):
        super().rotateRight(angle)
        self.wheelSystem.rotate(angle=angle)

    def stop(self):
        super().stop()
        self.wheelSystem.setWheelSpeeds(0, 0, 0, 0)
        self.wheelSystem.setWheelAngles(0, 0, 0, 0)
    
    def getFullLidarImage(self):
        return self.lidar.getImage()
        
    def getFrontLidarImage(self):
        return self.lidar.getPoints(90)
    
    def getLeftLidarImage(self):
        return self.lidar.getPoints(85, -90)
    
    def getRightLidarImage(self):
        return self.lidar.getPoints(85, 90)
    
    def getLidarImage(self,atDegree: int, fov: int):
        return self.lidar.getPoints(atDegree - (fov//2), fov)
    