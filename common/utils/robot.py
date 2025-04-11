import json


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
