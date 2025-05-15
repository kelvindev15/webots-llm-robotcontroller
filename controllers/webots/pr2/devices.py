from controller import Supervisor
from controllers.webots.adapters.motor import WBMotor
from controllers.webots.adapters.camera import WBCamera
from controllers.webots.adapters.lidar import WBLidar, WBTiltLidar
from simulation.observers import EventManager

class PR2Devices:
    """
    This class contains the devices of the PR2 robot.
    """

    def __init__(self, supervisor: Supervisor, eventManager: EventManager, timeStep=32):
        # SENSORS
        self.CAMERA = WBCamera(supervisor.getDevice("wide_stereo_r_stereo_camera_sensor"), timeStep)

        self.WHEEL_RADIUS = 0.08
        self.CENTER_TO_WHEEL = 0.318

        # WHEELS
        self.BACK_LEFT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("bl_caster_l_wheel_joint"), timeStep, eventManager)
        self.BACK_LEFT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("bl_caster_r_wheel_joint"), timeStep, eventManager)

        self.BACK_RIGHT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("br_caster_l_wheel_joint"), timeStep, eventManager)
        self.BACK_RIGHT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("br_caster_r_wheel_joint"), timeStep, eventManager)

        self.FRONT_LEFT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fl_caster_l_wheel_joint"), timeStep, eventManager)
        self.FRONT_LEFT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fl_caster_r_wheel_joint"), timeStep, eventManager)

        self.FRONT_RIGHT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fr_caster_l_wheel_joint"), timeStep, eventManager)
        self.FRONT_RIGHT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fr_caster_r_wheel_joint"), timeStep, eventManager)

        # CASTER WHEELS
        self.BACK_LEFT_CASTER: WBMotor = WBMotor(supervisor.getDevice("bl_caster_rotation_joint"), timeStep, eventManager)
        self.BACK_RIGHT_CASTER: WBMotor = WBMotor(supervisor.getDevice("br_caster_rotation_joint"), timeStep, eventManager)
        self.FRONT_LEFT_CASTER: WBMotor = WBMotor(supervisor.getDevice("fl_caster_rotation_joint"), timeStep, eventManager)
        self.FRONT_RIGHT_CASTER: WBMotor = WBMotor(supervisor.getDevice("fr_caster_rotation_joint"), timeStep, eventManager)

        # ARM
        self.RIGHT_SHOULDER_LIFT: WBMotor = WBMotor(supervisor.getDevice("r_shoulder_lift_joint"), timeStep, eventManager)
        self.RIGHT_ELBOW_FLEX: WBMotor = WBMotor(supervisor.getDevice("r_elbow_flex_joint"), timeStep, eventManager)

        self.LEFT_SHOULDER_LIFT: WBMotor = WBMotor(supervisor.getDevice("l_shoulder_lift_joint"), timeStep, eventManager)
        self.LEFT_ELBOW_FLEX: WBMotor = WBMotor(supervisor.getDevice("l_elbow_flex_joint"), timeStep, eventManager)

        # LASERS
        self.LASER_TILT: WBLidar = WBLidar(supervisor.getDevice("laser_tilt"), timeStep)
        self.LASER_TILT_JOINT: WBMotor = WBMotor(supervisor.getDevice("laser_tilt_mount_joint"), timeStep, eventManager)
        self.TILT_LIDAR: WBTiltLidar = WBTiltLidar(self.LASER_TILT, self.LASER_TILT_JOINT)
        
        self.BASE_LASER: WBLidar = WBLidar(supervisor.getDevice("base_laser"), timeStep)

        # HEAD
        self.HEAD_PAN_JOINT: WBMotor = WBMotor(supervisor.getDevice("head_pan_joint"), timeStep, eventManager)
        self.HEAD_TILT_JOINT: WBMotor = WBMotor(supervisor.getDevice("head_tilt_joint"), timeStep, eventManager)
