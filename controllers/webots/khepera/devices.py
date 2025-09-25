from controllers.webots.adapters.camera import WBCamera
from controllers.webots.adapters.motor import WBMotor
from controller import Supervisor
from simulation.observers import EventManager


class KhepheraDevices:
    def __init__(self, supervisor: Supervisor, eventManager: EventManager, timeStep=32):

        self.LEFT_WHEEL = WBMotor(supervisor.getDevice("left wheel motor"), timeStep, eventManager)
        self.RIGHT_WHEEL = WBMotor(supervisor.getDevice("right wheel motor"), timeStep, eventManager)

        self.CAMERA = WBCamera(supervisor.getDevice("camera"), timeStep)