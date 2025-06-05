import json
import numpy as np


def readSystemInstruction():
    with open('system_instruction.txt', 'r') as file:
        return file.read()


def readUserPrompt():
    with open('user_prompt.txt', 'r') as file:
        return file.read()


def saveRobotPose(robot):
    with open('robot_pose.json', 'w') as file:
        file.write(json.dumps(robot.getPose()))


def readRobotPose():
    with open('robot_pose.json', 'r') as file:
        return json.loads(file.read())


def readTargetPosition():
    with open('target_position.json', 'r') as file:
        return json.loads(file.read())
    
def getDistancesFromLidar(readings, fov_degrees):
    readings = np.array(readings)
    image_portion_angle = fov_degrees // 3
    points_per_degree = len(readings) / float(fov_degrees)
    left_end = int(points_per_degree * image_portion_angle)
    middle_end = int(points_per_degree * 2 * image_portion_angle)
    left = np.array(readings[:left_end])
    middle = np.array(readings[left_end:middle_end])
    right = np.array(readings[middle_end:])

    left_min_angle = -fov_degrees // 2
    left_max_angle = left_min_angle + image_portion_angle
    middle_min_angle = -image_portion_angle // 2
    middle_max_angle = image_portion_angle // 2
    right_min_angle = middle_max_angle
    right_max_angle = fov_degrees // 2

    return {
        "front_distance": readings[len(readings) // 2 - 3: len(readings) // 2 + 3].mean() if len(readings) > 6 else None,
        "left": {
            "minAngle": left_min_angle,
            "maxAngle": left_max_angle,
            "min_distance": float(np.min(left)) if left.size > 0 else None,
            "min_distance_angle": left_min_angle + (np.argmin(left) / max(len(left)-1,1)) * image_portion_angle if left.size > 0 else None
        },
        "middle": {
            "minAngle": middle_min_angle,
            "maxAngle": middle_max_angle,
            "min_distance": float(np.min(middle)) if middle.size > 0 else None,
            "min_distance_angle": middle_min_angle + (np.argmin(middle) / max(len(middle)-1,1)) * image_portion_angle if middle.size > 0 else None
        },
        "right": {
            "minAngle": right_min_angle,
            "maxAngle": right_max_angle,
            "min_distance": float(np.min(right)) if right.size > 0 else None,
            "min_distance_angle": right_min_angle + (np.argmin(right) / max(len(right)-1,1)) * image_portion_angle if right.size > 0 else None
        }
    }

def getDistanceDescription(distances):
    return f"""
    Lidar distances:
    - Front: {round(distances['front_distance'], 2) if distances['front_distance'] is not None else 'N/A'}
    - Left ([{distances['left']['minAngle']}, {distances['left']['maxAngle']}] degrees): {round(distances['left']['min_distance'], 2) if distances['left']['min_distance'] is not None else 'N/A'} at angle {np.round(distances['left']['min_distance_angle'])} degrees
    - Middle ([{distances['middle']['minAngle']}, {distances['middle']['maxAngle']}] degrees): {round(distances['middle']['min_distance'], 2) if distances['middle']['min_distance'] is not None else 'N/A'} at angle {np.round(distances['middle']['min_distance_angle'])} degrees
    - Right ([{distances['right']['minAngle']}, {distances['right']['maxAngle']}] degrees): {round(distances['right']['min_distance'], 2) if distances['right']['min_distance'] is not None else 'N/A'} at angle {np.round(distances['right']['min_distance_angle'])} degrees
    """.strip()
