from controller.lidar import Lidar
from typing import List
import numpy as np
from dataclasses import dataclass
from controllers.webots.adapters.motor import WBMotor
from typing import Callable
 
@dataclass
class LidarConfig:
    """Configuration parameters for Lidar"""
    horizontal_resolution: int
    fov_radians: float

    @property
    def fov_degrees(self) -> float:
        return np.rad2deg(self.fov_radians)
    
    @property
    def points_per_degree(self) -> float:
        return self.horizontal_resolution / self.fov_degrees

class LidarSnapshot:
    """Represents a snapshot of lidar distance measurements"""
    def __init__(self, distances: List[float]):
        self.distances = distances

    def __len__(self) -> int:
        return len(self.distances)

    def __getitem__(self, index) -> float:
        return self.distances[index]

    def __iter__(self):
        return iter(self.distances)
    
    def __repr__(self) -> str:
        return f"LidarSnapshot with {len(self.distances)} points"
    
    def __str__(self) -> str:
        return f"LidarSnapshot({self.distances})"

class WBLidar:
    """Webots Lidar adapter with simplified point cloud handling"""
    def __init__(self, lidar: 'Lidar', time_step: int):
        self.lidar = lidar
        self.lidar.enable(time_step)
        self.lidar.enablePointCloud()
        self.config = LidarConfig(
            horizontal_resolution=self.lidar.getHorizontalResolution(),
            fov_radians=self.lidar.getFov()
        )

    def getPoints(self, fov_degrees: int, rotation_degrees: int = 0) -> LidarSnapshot:
        """Get lidar points within specified FOV and rotation
        
        Args:
            fov_degrees: Field of view in degrees
            rotation_degrees: Rotation offset in degrees
        
        Returns:
            LidarSnapshot containing the requested points
        """
        self._validate_params(fov_degrees, rotation_degrees)
        
        if fov_degrees == 0:
            return self._get_single_point(rotation_degrees)
        
        return self._get_point_range(fov_degrees, rotation_degrees)

    def _validate_params(self, fov_degrees: int, rotation_degrees: int) -> None:
        """Validate FOV and rotation parameters"""
        if not 0 <= fov_degrees < self.config.fov_degrees:
            raise ValueError(f"FOV must be between 0 and {self.config.fov_degrees} degrees")
        
        max_rotation = self.config.fov_degrees - fov_degrees
        if not -max_rotation <= rotation_degrees <= max_rotation:
            raise ValueError(f"Invalid rotation for given FOV")

    def _get_single_point(self, rotation_degrees: int) -> LidarSnapshot:
        """Get single point measurement at specified rotation"""
        midpoint = self._get_midpoint(rotation_degrees)
        return LidarSnapshot([self.getImage()[midpoint]])

    def _get_point_range(self, fov_degrees: int, rotation_degrees: int) -> LidarSnapshot:
        """Get range of points for specified FOV and rotation"""
        midpoint = self._get_midpoint(rotation_degrees)
        offset = int(self.config.points_per_degree * (fov_degrees / 2))
        
        start = max(midpoint - offset, 0)
        end = min(midpoint + offset, self.config.horizontal_resolution - 1)
        
        return LidarSnapshot(self.getImage()[int(start):int(end)])

    def _get_midpoint(self, rotation_degrees: int) -> int:
        """Calculate midpoint index for given rotation"""
        rotation_offset = int(self.config.points_per_degree * rotation_degrees)
        return (self.config.horizontal_resolution // 2) + rotation_offset

    def getImage(self) -> List[float]:
        """Get reversed range image from lidar"""
        return list(reversed(self.lidar.getRangeImage()))
    
class WBTiltLidar:
    def __init__(self, lidar: WBLidar, motor: WBMotor):
        self.lidar = lidar
        self.motor = motor

    @property
    def maxTiltPosition(self) -> float:
        return self.motor.maxPosition
    
    @property
    def minTiltPosition(self) -> float:
        return self.motor.minPosition
    
    def setPositionByPercentage(self, percent: float, onComplete: Callable[[None], None] = None):
        self.motor.setPositionByPercentage(percent, onComplete)

    def getPositionPercent(self) -> float:
        return self.motor.getPositionPercent()    