from controllers.webots.pr2.wheels import PR2WheelSystem, PR2Wheel
from controllers.webots.WBRobotController import WBRobotController
from simulation.observers import EventManager, EventType, EventData
from controllers.webots.pr2.devices import PR2Devices

class PR2Controller(WBRobotController):

    def __init__(self, devices: PR2Devices, eventManager: EventManager=None):
        super().__init__()
        self.devices = devices
        self.camera = devices.CAMERA
        self.lidar = devices.BASE_LASER
        self.wheelSystem = PR2WheelSystem(devices, eventManager)
        self.__initializeArms()
        self.eventManager = eventManager
        eventManager.subscribe(EventType.SIMULATION_STEP, self.__onSimulationStep)
        
    def __onSimulationStep(self, _: EventData):
        self.devices.HEAD_PAN_JOINT.setPositionByPercentage(0.5)
        self.devices.HEAD_PAN_JOINT.setSpeed(PR2Wheel.MAX_SPEED)

    def __initializeArms(self):
        self.devices.LEFT_SHOULDER_LIFT.toMinPosition()
        self.devices.RIGHT_SHOULDER_LIFT.toMinPosition()
        self.devices.LEFT_ELBOW_FLEX.toMinPosition()
        self.devices.RIGHT_ELBOW_FLEX.toMinPosition()

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
        self.wheelSystem.stop()
    
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
    