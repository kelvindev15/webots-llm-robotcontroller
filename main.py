from common.llm.chats import GeminiChat, OllamaChat, OpenAIChat
from common.robot.LLMRobotController import LLMRobotController
from controllers.webots.pr2.PR2Controller import PR2Controller
from controllers.webots.keyboard import KeyboardController
from controller import Keyboard, Supervisor
import json
from common.utils.robot import readSystemInstruction, readUserPrompt
from common.utils.images import plotDetections
from dotenv import load_dotenv
from simulation.observers import EventManager
import cv2
import logging

load_dotenv()
rootLogger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

TIME_STEP = 64
MAX_SPEED = 6.28
eventManager = EventManager()
supervisor = Supervisor()
robot = PR2Controller(supervisor, TIME_STEP, eventManager)
geminiChat = GeminiChat(system_instruction=readSystemInstruction())
ollamaChat = OllamaChat(model_name="gemma3:4b", system_instruction=readSystemInstruction())
openaiChat = OpenAIChat(system_instruction=readSystemInstruction())
robotChat = geminiChat
llmController = LLMRobotController(robot, robotChat)

keyboard = Keyboard()
keyboard.enable(TIME_STEP)

image = None
initialPose = None

def handle_keyboard_input(key, robot, initial_pose):
    if ord('0') <= key <= ord('9'):
        execute_plan(key - ord('0'), robot, initial_pose)

def execute_plan(plan_number, robot, initial_pose):
    try:
        with open(f'plan_{plan_number}.json', 'r') as file:
            plan = json.loads(file.read())
        robot.setPosition(initial_pose["position"])
        robot.setRotation(initial_pose["rotation"])
        robot.executePlan(plan)
        print("Plan execution terminated")
    except Exception as e:
        print(f"Error executing plan {plan_number}: {str(e)}")

robotKeyboardController = KeyboardController()
robotKeyboardController.onNoKey(lambda: robot.stop())
robotKeyboardController.onKey(keyboard.RIGHT, lambda: robot.rotateRight(90))
robotKeyboardController.onKey(keyboard.UP, lambda: robot.goFront(1.0))
robotKeyboardController.onKey(keyboard.DOWN, lambda: robot.goBack(1.0))
robotKeyboardController.onKey(keyboard.LEFT, lambda: robot.rotateLeft(90))

simulationKeyboardController = KeyboardController()
simulationKeyboardController.onKey(ord('P'), lambda: llmController.ask(readUserPrompt()))
simulationKeyboardController.onKey(ord('L'), lambda: print("Front Lidar:", robot.getFrontLidarImage()))
def onStep(data):
    image = robot.getCameraImage()
    cv2.imshow("Camera", plotDetections(image))
    cv2.waitKey(1)
eventManager.subscribe("step", onStep)
while robot.doStep() != -1:
    if initialPose is None:
        initialPose = {
            "position": robot.getPosition(),
            "rotation": robot.getRotation()
        }
    pressed_key = keyboard.getKey()    
    simulationKeyboardController.execute(pressed_key)
    if not robotKeyboardController.execute(pressed_key):
        robot.stop() 
    handle_keyboard_input(keyboard.getKey(), robot, initialPose)
cv2.destroyAllWindows()
