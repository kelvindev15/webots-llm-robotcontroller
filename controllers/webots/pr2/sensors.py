from controller import Supervisor

class PR2SensorSystem:
    def __init__(self, supervisor: Supervisor, timeStep: int):
        self._initialize_cameras(supervisor, timeStep)
        self._initialize_lidar(supervisor, timeStep)

    def _initialize_cameras(self, supervisor: Supervisor, timeStep: int) -> None:
        self.camera = supervisor.getDevice("wide_stereo_l_stereo_camera_sensor")
        self.r_camera = supervisor.getDevice("wide_stereo_r_stereo_camera_sensor")
        self.camera.enable(timeStep)
        self.r_camera.enable(timeStep)

    def _initialize_lidar(self, supervisor: Supervisor, timeStep: int) -> None:
        self.lidar = supervisor.getDevice("base_laser")
        self.lidar.enable(timeStep)
        self.lidar.enablePointCloud()