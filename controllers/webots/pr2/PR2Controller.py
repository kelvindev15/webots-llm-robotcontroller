from controller import Supervisor
from common.robot.RobotController import RobotController
import numpy as np
from controllers.webots.adapters.lidar import WBLidar
from controllers.webots.adapters.camera import WBCamera
from controllers.webots.pr2.wheels import PR2WheelSystem

class PR2Controller(RobotController):

    def __init__(self, supervisor: Supervisor, timeStep=32, max_speed=6.28):
        self.wheelSystem = PR2WheelSystem(supervisor, timeStep)
        super().__init__(max_speed)
        self.supervisor: Supervisor = supervisor
        self.camera = WBCamera(self.supervisor.getDevice("wide_stereo_r_stereo_camera_sensor"), timeStep)
        self.lidar = WBLidar(self.supervisor.getDevice("base_laser"), timeStep)
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

    def moveForward(self, speed=1.0):
        super().moveForward()
        self.wheelSystem.setWheelSpeeds(speed, speed, speed, speed)

    def moveBackward(self, speed=1.0):
        super().moveBackward()
        self.wheelSystem.setWheelSpeeds(-speed, -speed, -speed, -speed)

    def turnRight(self, speed=1.0):
        super().turnRight()
        self.wheelSystem.setWheelAngles(np.pi/4, -np.pi/4, -np.pi/4, np.pi/4)
        self.wheelSystem.setWheelSpeeds(speed, -speed, speed, -speed)

    def turnLeft(self, speed=1.0):
        super().turnLeft()
        self.wheelSystem.setWheelAngles(np.pi/4, -np.pi/4, -np.pi/4, np.pi/4)
        self.wheelSystem.setWheelSpeeds(-speed, speed, -speed, speed)

    def stopMoving(self):
        super().stopMoving()
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
    
    def getCameraImage(self):
        return self.camera.getImage()
