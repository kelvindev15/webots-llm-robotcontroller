import numpy as np
from common.utils.geometry import angleBetweenVectors, distanceBetweenPoints
from controller import Supervisor
from controller.wb import wb
from enum import Enum

from controllers.webots.adapters.rotation import WbRotation

class SceneObjects(Enum):
    ROBOT = "ROBOT"
    FIRE_EXTINGUISHER = "FIRE_EXTINGUISHER"
    PLASTIC_CRATE = "PLASTIC_CRATE"
    OIL_BARREL = "OIL_BARREL"
    WOODEN_PALLET = "WOODEN_PALLET"
    PALLET_STACK = "PALLET_STACK"
    TABLE = "TABLE"
    WOODEN_BOX = "WOODEN_BOX"
    OPEN_CABINET = "OPEN_CABINET"
    CLOSED_CABINET = "CLOSED_CABINET"
    STAIRS = "STAIRS"
    
def getPositionOf(supervisor: Supervisor, object: SceneObjects):
    node = supervisor.getFromDef(object.value)
    if node:
        return { "x": node.getPosition()[0], "y": node.getPosition()[1], "z": node.getPosition()[2] }
    return None

def distanceBetween(supervisor: Supervisor, object1: SceneObjects, object2: SceneObjects):
    pos1 = getPositionOf(supervisor, object1)
    pos2 = getPositionOf(supervisor, object2)
    return distanceBetweenPoints([pos1["x"], pos1["y"]], [pos2["x"], pos2["y"]])

def getDirectionVersorOf(supervisor: Supervisor, object: SceneObjects):
    node = supervisor.getFromDef(object.value)
    
    if node:
        versor = np.array(node.getOrientation()).reshape((3,3)).dot(np.array([1, 0, 0]).reshape((3,1)))
        return { "x": versor[0, 0], "y": versor[1, 0] }
    
def getAngleBetweenRobotAndObject(supervisor: Supervisor, object: SceneObjects):
    if object == SceneObjects.ROBOT:
        return 0
    robot = supervisor.getFromDef(SceneObjects.ROBOT.value)
    target = supervisor.getFromDef(object.value)
    
    object_position = getPositionOf(supervisor, object)
    robot_position = getPositionOf(supervisor, SceneObjects.ROBOT)
    robot_direction = getDirectionVersorOf(supervisor, SceneObjects.ROBOT)
    if robot and target and object_position and robot_position and robot_direction:
        vector_to_object = np.array([object_position["x"] - robot_position["x"], object_position["y"] - robot_position["y"]])
        vector_to_object = vector_to_object / np.linalg.norm(vector_to_object)  # Normalize
        return angleBetweenVectors([robot_direction["x"], robot_direction["y"]], vector_to_object)
    return None

def distanceScore(supervisor: Supervisor, object1: SceneObjects, object2: SceneObjects):
    distance = distanceBetween(supervisor, object1, object2)
    if distance <= 2.5:
        return 1
    else:
        return 1.5 ** -(distance - 2.5)
    
def headingScore(supervisor: Supervisor, object: SceneObjects):
    angle = getAngleBetweenRobotAndObject(supervisor, object)
    return (np.pi - angle)/np.pi if angle is not None else 0

def getScore(supervisor: Supervisor, object: SceneObjects):
    distance = distanceScore(supervisor, SceneObjects.ROBOT, object)
    heading = headingScore(supervisor, object)
    return distance * heading