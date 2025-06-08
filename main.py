from common.llm.chats import GeminiChat, OllamaChat, OpenAIChat
from common.robot.LLMRobotController import LLMRobotController
from common.utils.environment import getRobotPose, setRobotPose
from controllers.webots.pr2.PR2Controller import PR2Controller
from controllers.webots.pr2.devices import PR2Devices
from controllers.webots.keyboard import KeyboardController
from controller import Keyboard, Supervisor
from common.utils.robot import readSystemInstruction, readUserPrompt
from common.utils.images import box_label, detectObjects, toBase64Image
from common.utils.llm import create_message
from common.utils.misc import extractJSON
from dotenv import load_dotenv
from simulation import LLMSession
from simulation.observers import EventManager
from simulation.events import EventType, StepEventData
import cv2
import json
import logging
import datetime

from simulation.sim import LLMObserver

load_dotenv()
rootLogger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)

TIME_STEP = 64
MAX_SPEED = 6.28
eventManager = EventManager()
supervisor = Supervisor()
llmObserver = LLMObserver(supervisor,eventManager)
pr2Devices = PR2Devices(supervisor, eventManager, TIME_STEP)
robot = PR2Controller(pr2Devices, eventManager)
geminiChat = GeminiChat()
ollamaChat = OllamaChat(model_name="gemma3:4b")
openaiChat = OpenAIChat()
robotChat = geminiChat
robotChat.set_system_instruction(readSystemInstruction())
llmController = LLMRobotController(robot, robotChat, eventManager)

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
robotKeyboardController.onKey(keyboard.RIGHT, lambda: robot.rotateRight(90))
robotKeyboardController.onKey(keyboard.UP, lambda: robot.goFront(1.0))
robotKeyboardController.onKey(keyboard.DOWN, lambda: robot.goBack(1.0))
robotKeyboardController.onKey(keyboard.LEFT, lambda: robot.rotateLeft(90))
robotKeyboardController.onKey(ord('W'), lambda: robot.goFront(None))
robotKeyboardController.onKey(ord('A'), lambda: robot.rotateLeft(None))
robotKeyboardController.onKey(ord('S'), lambda: robot.goBack(None))
robotKeyboardController.onKey(ord('D'), lambda: robot.rotateRight(None))
robotKeyboardController.onKey(ord('Q'), lambda: robot.stop())

boundingBoxPrompt = """
Output the objects bounding boxes in the image in json format.
The json should be a list of objects, each object should have the following properties:
- cls: the name of the object
- conf: the confidence of the detection
- x: the x coordinate of the center of the bounding box
- y: the y coordinate of the center of the bounding box
- w: the width of the bounding box
- h: the height of the bounding box

The json should be in the following format:
[
    {
        "name": "object_name",
        "confidence": 0.9,
        "x": 100,
        "y": 300,
        "w": 40,
        "h": 20
    },
    ...
]

Output the json without any additional text.

"""

def llmBoundingBox():
    image = robot.getCameraImage()
    response = robotChat.send_message(create_message(boundingBoxPrompt, toBase64Image(image)))
    detections = json.loads(extractJSON(response))
    for detection in detections:
        image = box_label(image, ((detection["x"] - 0.5 * detection["w"]), (detection["y"] - 0.5 * detection["h"]), (detection["x"] + 0.5 * detection["w"]), (detection["y"] + 0.5 * detection["h"])), detection["cls"], (0, 255, 0), (255, 255, 255))
    cv2.imshow("Camera", image)
    cv2.waitKey(1)

def multipleSimulation():
    with open("simulation_prompts.txt", "r") as file:
        prompts = file.readlines()
        pose = getRobotPose(supervisor)
    n_experiments = len(prompts)
    current_experiment = 0
    def next_experiment(_):
        nonlocal current_experiment
        nonlocal pose
        current_experiment += 1
        if current_experiment < n_experiments:
            setRobotPose(supervisor, pose)
            supervisor.step(TIME_STEP)
            print(f"Running experiment {current_experiment + 1}/{n_experiments}")
            llmController.ask(prompts[current_experiment].strip(), maxIterations=30)
        else:
            print("All experiments completed.")
            eventManager.unsubscribe(next_experiment)
    eventManager.subscribe(EventType.LLM_SESSION_COMPLETED, next_experiment)
    print(f"Running experiment {current_experiment + 1}/{n_experiments}")
    llmController.ask(prompts[current_experiment].strip(), maxIterations=30)
        
simulationKeyboardController = KeyboardController()
simulationKeyboardController.onKey(ord('P'), lambda: llmController.ask(readUserPrompt()))
simulationKeyboardController.onKey(ord('L'), lambda: print("Front Lidar:", robot.getFrontLidarImage()))
simulationKeyboardController.onKey(ord('B'), lambda: multipleSimulation())

def onStep(_: StepEventData):
    image = robot.getCameraImage()
    detections = detectObjects(image)
    for detection in detections:
        image = box_label(image, ((detection.x - 0.5 * detection.w), (detection.y - 0.5 * detection.h), (detection.x + 0.5 * detection.w), (detection.y + 0.5 * detection.h)), detection.cls, (0, 255, 0), (255, 255, 255))
    cv2.imshow("Camera", image)
    cv2.waitKey(1)

# eventManager.subscribe(EventType.SIMULATION_STEP, onStep)
def save_session(session: LLMSession):
    # create a YYYY_MM-DD_HH-MM-SS format for the session ID
    filename = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    with open(f"experiments/experiment_{filename}.json", "w") as file:
        json.dump(session.asObject(), file, indent=4)
    print("Session saved:", session.id)
eventManager.subscribe(EventType.LLM_SESSION_COMPLETED, save_session)
step_counter = 0
while supervisor.step(TIME_STEP) != -1:
    eventManager.notify(EventType.SIMULATION_STEP, StepEventData(step_counter))
    pressed_key = keyboard.getKey()    
    simulationKeyboardController.execute(pressed_key)
    if not(robotKeyboardController.execute(pressed_key)):
        robot.stop()
    handle_keyboard_input(keyboard.getKey(), robot, initialPose)
    step_counter += 1
cv2.destroyAllWindows()
