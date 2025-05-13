from common.llm.chats import GeminiChat, OllamaChat
from common.robot.LLMRobotController import LLMRobotController
from common.robot.khepera.KheperaController import KheperaController
from controller import Keyboard, Supervisor
import json
from common.utils.experiments import replaySimulation
from common.utils.images import toBase64Image
from common.utils.llm import create_message
from common.utils.robot import readRobotPose, readSystemInstruction, readTargetPosition, readUserPrompt, saveRobotPose


TIME_STEP = 64
MAX_SPEED = 12.56

supervisor = Supervisor()
robot = KheperaController(supervisor, TIME_STEP, MAX_SPEED)
geminiChat = GeminiChat(system_instruction=readSystemInstruction())
llavaChat = OllamaChat(system_instruction=readSystemInstruction())
robotChat = geminiChat
llmController = LLMRobotController(robot, robotChat)

keyboard = Keyboard()
keyboard.enable(TIME_STEP*2)

image = None
initialPose = None
while supervisor.step(TIME_STEP) != -1:
    if initialPose is None:
        initialPose = {
            "position": robot.getPosition(),
            "rotation": robot.getRotation()
        }
    key = keyboard.getKey()
    attempt = 0
    last_command = None
    while key != -1:
        attempt = attempt + 1
        if key == keyboard.UP or key == ord('W'):
            last_command = "UP"
            robot.moveForward(2)
        elif key == keyboard.DOWN or key == ord('S'):
            last_command = "DOWN"
            robot.moveForward(-2)

        if key == ord('A'):
            robot.turnLeft(1.0)
        elif key == ord('D'):
            robot.turnRight(1.0)

        for i in range(10):
            if key == ord(str(i)):
                plan = None
                with open('plan_' + str(i) + '.json', 'r') as file:
                    plan = json.loads(file.read())
                robot.setPosition(initialPose["position"])
                robot.setRotation(initialPose["rotation"])
                robot.executePlan(plan)
                print("Plan execution terminated")

        if key == ord('Q'):
            print(robotChat.generate([create_message("What do you see?",
                  toBase64Image(robot.getCameraImage()))]))
        elif key == ord('P'):
            prompt = readUserPrompt()
            llmController.ask(prompt)
        elif key == ord('R'):
            # read a number from the 'simulation_to_reproduce.txt' file
            with open('simulation_to_reproduce.txt', 'r') as file:
                n = int(file.read())
            replaySimulation(n, llmController)
        elif key == ord('T'):
            saveRobotPose(robot)
            print("Robot pose saved")
        elif key == ord('Y'):
            robot.setPose(readRobotPose())
            print("Robot pose restored")
        elif key == ord('I'):
            target = readTargetPosition()
            print(robot.calculateTargetReachingAccuracy(
                target["x"], target["y"]))
        key = keyboard.getKey()

    if attempt == 0:
        robot.stopMoving()
        last_command = None
    elif attempt == 1:
        if last_command in set(["LEFT", "RIGHT"]):
            robot.stopMoving()
        elif last_command in set(["UP", "DOWN"]):
            # robot.restoreWheelAngles()
            pass
    pass
