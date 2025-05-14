from common.robot.RobotController import RobotController
from controllers.webots.adapters.camera import WBCamera


# self.supervisor.getSelf().getField("translation").getSFVec3f()
# self.supervisor.getSelf().getField("rotation").getSFRotation()
class WBRobotController(RobotController):
    def __init__(self):
        self.camera: WBCamera = None

    def getCameraImage(self):
        if self.camera is None:
            raise Exception("Camera not yet initialized")
        return self.camera.getImage()