import numpy as np
from typing import List
from controller import Supervisor
import random
import math

OBSTACLES = ["CLOSED_CABINET", "OPEN_CABINET", "TABLE", 
             "PLASTIC_CRATE", "PALLET_STACK", "SINGLE_PALLET_STACK",
             "BOX_1", "WOODEN_BOX", "BOX_2", "WOODEN_PALLET", "STAIRS",
             "FIRE_EXTINGUISHER", "OIL_BARREL", "BARREL_1"
]

def rotateVector(vector, angle):
    rotation_matrix = np.array(
        [[np.cos(angle), -np.sin(angle)],
         [np.sin(angle), np.cos(angle)]])
    return np.dot(rotation_matrix, vector)

def angleBetweenVectors(v1, v2):
    u = np.array(v1)
    v = np.array(v2)
    dot_product = np.dot(u, v)

    dot_product = np.clip(dot_product, -1.0, 1.0)

    angle = np.arccos(dot_product)

    return angle  # in radians

def normalizeVector(vector):
    return vector / np.linalg.norm(vector)

def distanceBetweenPoints(p1: List[float], p2: List[float]):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def find_safe_position(supervisor: Supervisor, max_attempts=100):
    def getEnvironmentBounds():
        # Center is at [0, -4.34], size [20, 16.32]
        return {
            "origin": [0, -4.34],
            "min": [-8, -10.5],
            "max": [8, 1.82]
        }

    def random_position(bounds):
        min = bounds["min"]
        max = bounds["max"]
        x = random.uniform(min[0], max[0])
        y = random.uniform(min[1], max[1])
        return [x, y]

    def is_collision(pos, obstacles, min_dist=0.5):
        for obj in obstacles:
            obj_pos = supervisor.getFromDef(obj).getField("translation").getSFVec3f()
            dx, dy = pos[0]-obj_pos[0], pos[1]-obj_pos[1]
            if math.hypot(dx, dy) < min_dist:
                return True
        return False
    
    for _ in range(max_attempts):
        pos = random_position(getEnvironmentBounds())
        if not(is_collision(pos, OBSTACLES)):
            return pos
    print("No safe position found")
    return None
