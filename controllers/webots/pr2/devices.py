from controller import Supervisor
from controllers.webots.adapters.motor import WBMotor
from controllers.webots.adapters.camera import WBCamera
from controllers.webots.adapters.lidar import WBLidar

class PR2Devices:
    """
    This class contains the devices of the PR2 robot.
    """

    def __init__(self, supervisor: Supervisor, timeStep=32):
        # SENSORS
        self.CAMERA = WBCamera(supervisor.getDevice("wide_stereo_r_stereo_camera_sensor"), timeStep)

        WHEEL_MIN_POSITION = -3.14
        WHEEL_MAX_POSITION = 3.14

        ELBOW_FLEX_MIN_POSITION = -2.32
        ELBOW_FLEX_MAX_POSITION = 0.0
        
        SHOULDER_LIFT_MIN_POSITION = -0.52
        SHOULDER_LIFT_MAX_POSITION = 1.4

        LASER_TILT_MIN_POSITION = -0.79
        LASER_TILT_MAX_POSITION = 1.48

        HEAD_PAN_MIN_POSITION = -3.01
        HEAD_PAN_MAX_POSITION = 3.01
        HEAD_TILT_MIN_POSITION = -0.47
        HEAD_TILT_MAX_POSITION = 1.4

        self.WHEEL_RADIUS = 0.08
        self.CENTER_TO_WHEEL = 0.318

        # WHEELS
        self.BACK_LEFT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("bl_caster_l_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.BACK_LEFT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("bl_caster_r_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)

        self.BACK_RIGHT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("br_caster_l_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.BACK_RIGHT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("br_caster_r_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)

        self.FRONT_LEFT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fl_caster_l_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.FRONT_LEFT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fl_caster_r_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)

        self.FRONT_RIGHT_LEFT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fr_caster_l_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.FRONT_RIGHT_RIGHT_WHEEL: WBMotor = WBMotor(supervisor.getDevice("fr_caster_r_wheel_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)

        # CASTER WHEELS
        self.BACK_LEFT_CASTER: WBMotor = WBMotor(supervisor.getDevice("bl_caster_rotation_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.BACK_RIGHT_CASTER: WBMotor = WBMotor(supervisor.getDevice("br_caster_rotation_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.FRONT_LEFT_CASTER: WBMotor = WBMotor(supervisor.getDevice("fl_caster_rotation_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)
        self.FRONT_RIGHT_CASTER: WBMotor = WBMotor(supervisor.getDevice("fr_caster_rotation_joint"), timeStep, WHEEL_MIN_POSITION, WHEEL_MAX_POSITION)

        # ARM
        self.RIGHT_SHOULDER_LIFT: WBMotor = WBMotor(supervisor.getDevice("r_shoulder_lift_joint"), timeStep, SHOULDER_LIFT_MIN_POSITION, SHOULDER_LIFT_MAX_POSITION)
        self.RIGHT_ELBOW_FLEX: WBMotor = WBMotor(supervisor.getDevice("r_elbow_flex_joint"), timeStep, ELBOW_FLEX_MIN_POSITION, ELBOW_FLEX_MAX_POSITION)
        
        self.LEFT_SHOULDER_LIFT: WBMotor = WBMotor(supervisor.getDevice("l_shoulder_lift_joint"), timeStep, SHOULDER_LIFT_MIN_POSITION, SHOULDER_LIFT_MAX_POSITION)
        self.LEFT_ELBOW_FLEX: WBMotor = WBMotor(supervisor.getDevice("l_elbow_flex_joint"), timeStep, ELBOW_FLEX_MIN_POSITION, ELBOW_FLEX_MAX_POSITION)

        # LASERS
        self.LASER_TILT: WBLidar = WBLidar(supervisor.getDevice("laser_tilt"), timeStep)
        self.BASE_LASER: WBLidar = WBLidar(supervisor.getDevice("base_laser"), timeStep)
        self.LASER_TILT_JOINT: WBMotor = WBMotor(supervisor.getDevice("laser_tilt_mount_joint"), timeStep, LASER_TILT_MIN_POSITION, LASER_TILT_MAX_POSITION)

        # HEAD
        self.HEAD_PAN_JOINT: WBMotor = WBMotor(supervisor.getDevice("head_pan_joint"), timeStep, HEAD_PAN_MIN_POSITION, HEAD_PAN_MAX_POSITION)
        self.HEAD_TILT_JOINT: WBMotor = WBMotor(supervisor.getDevice("head_tilt_joint"), timeStep, HEAD_TILT_MIN_POSITION, HEAD_TILT_MAX_POSITION)
