from typing import Dict, List, Optional, Any
import json
import numpy as np
from numpy.typing import NDArray

# File I/O operations
def readSystemInstruction() -> str:
    """Read system instructions from file."""
    with open('system_instruction.txt', 'r') as file:
        return file.read()

def readUserPrompt() -> str:
    """Read user prompt from file."""
    with open('user_prompt.txt', 'r') as file:
        return file.read()

def save_robot_pose(robot: Any) -> None:
    """Save robot pose to JSON file."""
    with open('robot_pose.json', 'w') as file:
        json.dump(robot.get_pose(), file)

def read_robot_pose() -> Dict[str, Any]:
    """Read robot pose from JSON file."""
    with open('robot_pose.json', 'r') as file:
        return json.load(file)

def read_target_position() -> Dict[str, Any]:
    """Read target position from JSON file."""
    with open('target_position.json', 'r') as file:
        return json.load(file)

# LIDAR data processing
class LidarSection:
    def __init__(self, min_angle: float, max_angle: float, readings: NDArray):
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.readings = readings
        self.min_distance = float(np.min(readings)) if readings.size > 0 else None
        self.min_distance_angle = (
            min_angle + (np.argmin(readings) / max(len(readings)-1, 1)) * (max_angle - min_angle)
            if readings.size > 0 else None
        )

    def to_dict(self) -> Dict[str, Optional[float]]:
        return {
            "minAngle": self.min_angle,
            "maxAngle": self.max_angle,
            "min_distance": self.min_distance,
            "min_distance_angle": self.min_distance_angle
        }

def getDistancesFromLidar(readings: List[float], fov_degrees: int) -> Dict[str, Any]:
    """
    Process LIDAR readings and return structured distance data.
    
    Args:
        readings: Raw LIDAR distance readings
        fov_degrees: Field of view in degrees
    
    Returns:
        Dictionary containing processed LIDAR data by sections
    """
    readings_array = np.array(readings)
    section_angle = fov_degrees // 3
    points_per_degree = len(readings) / float(fov_degrees)
    
    # Split readings into sections
    left_end = int(points_per_degree * section_angle)
    middle_end = int(points_per_degree * 2 * section_angle)
    
    sections = {
        "left": LidarSection(
            -fov_degrees // 2,
            -fov_degrees // 2 + section_angle,
            readings_array[:left_end]
        ),
        "middle": LidarSection(
            -section_angle // 2,
            section_angle // 2,
            readings_array[left_end:middle_end]
        ),
        "right": LidarSection(
            section_angle // 2,
            fov_degrees // 2,
            readings_array[middle_end:]
        )
    }
    
    return {
        "front_distance": (
            readings_array[len(readings) // 2 - 3: len(readings) // 2 + 3].mean()
            if len(readings) > 6 else None
        ),
        **{key: section.to_dict() for key, section in sections.items()}
    }

def format_distance_reading(value: Optional[float], precision: int = 2) -> str:
    """Format a distance reading with specified precision."""
    return f"{round(value, precision)}" if value is not None else "N/A"

def getDistanceDescription(distances: Dict[str, Any]) -> str:
    """Generate a human-readable description of LIDAR distances."""
    template = """
    Lidar distances:
      - Front: {front}
      - Left ([{left_range}] degrees): {left_dist} at angle {left_angle} degrees
      - Middle ([{mid_range}] degrees): {mid_dist} at angle {mid_angle} degrees
      - Right ([{right_range}] degrees): {right_dist} at angle {right_angle} degrees
    """
    
    return template.format(
        front=format_distance_reading(distances['front_distance']),
        left_range=f"{distances['left']['minAngle']}, {distances['left']['maxAngle']}",
        left_dist=format_distance_reading(distances['left']['min_distance']),
        left_angle=np.round(distances['left']['min_distance_angle']),
        mid_range=f"{distances['middle']['minAngle']}, {distances['middle']['maxAngle']}",
        mid_dist=format_distance_reading(distances['middle']['min_distance']),
        mid_angle=np.round(distances['middle']['min_distance_angle']),
        right_range=f"{distances['right']['minAngle']}, {distances['right']['maxAngle']}",
        right_dist=format_distance_reading(distances['right']['min_distance']),
        right_angle=np.round(distances['right']['min_distance_angle'])
    )
