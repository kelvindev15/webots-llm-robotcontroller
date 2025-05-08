from common.llm.chats import GeminiChat, LLavaChat, OpenAIChat
from common.robot.LLMRobotController import LLMRobotController
from controllers.webots.pr2.PR2Controller import PR2Controller
from controllers.webots.adapters.lidar import LidarSnapshot
from controller import Keyboard, Supervisor
import json
from common.utils.experiments import replaySimulation
from common.utils.images import toBase64Image
from common.utils.llm import create_message
from common.utils.robot import readRobotPose, readSystemInstruction, readTargetPosition, readUserPrompt, saveRobotPose
from dotenv import load_dotenv
import cv2
from ultralytics import YOLO
from typing import List
from common.types.ObjectDetection import ObjectDetection

load_dotenv()

# PR2 robot parameters
TIME_STEP = 64
MAX_SPEED = 6.28

# Khepera robot parameters
# TIME_STEP = 64
# MAX_SPEED = 12.56

supervisor = Supervisor()
robot = PR2Controller(supervisor, TIME_STEP, MAX_SPEED)
geminiChat = GeminiChat(system_instruction=readSystemInstruction())
llavaChat = LLavaChat(system_instruction=readSystemInstruction())
openaiChat = OpenAIChat(system_instruction=readSystemInstruction())
robotChat = geminiChat
llmController = LLMRobotController(robot, robotChat)

keyboard = Keyboard()
keyboard.enable(TIME_STEP*2)
model = YOLO("yolo11n.pt")  # initialize model


image = None
initialPose = None

def detectObjects(image):
    results = model(image, verbose=False)
    detections: List[ObjectDetection] = []
    for result in results:
        for box in result.boxes:
            x, y, w, h = box.xywhn[0]
            detections.append(ObjectDetection(
                model.names[int(box.cls.item())], 
                box.conf.item(), 
                x.item(), 
                y.item(), 
                w.item(), 
                h.item())
            )        
    return detections

def getObjectDistance(detection: ObjectDetection, lidarSnapshot: LidarSnapshot):
    return lidarSnapshot[round(detection.x)]

def printDistances():
    objects = detectObjects(robot.getCameraImage())
    lidarSnap = robot.getFrontLidarImage()
    for o in objects:
        print(f"Object: {o.cls}, Distance: {getObjectDistance(o, lidarSnap)}")

def handle_keyboard_input(key, robot, initial_pose):
    """Handle keyboard controls for robot movement and actions"""
    if key == -1:
        robot.stopMoving()
        return
        
    # Movement controls
    movement_controls = {
        keyboard.LEFT: lambda: robot.turnLeft(1.0),
        keyboard.RIGHT: lambda: robot.turnRight(1.0),
        keyboard.UP: lambda: robot.moveForward(1.0),
        keyboard.DOWN: lambda: robot.moveForward(-1.0),
        ord('W'): lambda: robot.moveForward(1.0),
        ord('S'): lambda: robot.moveForward(-1.0),
        ord('A'): lambda: robot.turnLeft(1.0),
        ord('D'): lambda: robot.turnRight(1.0),
    }
    
    # Special action controls
    action_controls = {
        ord('Q'): lambda: print(robotChat.generate([create_message("What do you see?", toBase64Image(robot.getCameraImage()))])),
        ord('P'): lambda: llmController.ask(readUserPrompt()),
        ord('T'): lambda: (saveRobotPose(robot), print("Robot pose saved")),
        ord('Y'): lambda: (robot.setPose(readRobotPose()), print("Robot pose restored")),
        ord('L'): lambda: print("Front Lidar:", robot.getFrontLidarImage()),
        ord('V'): lambda: print_object_detection(robot),
        ord('G'): lambda: printDistances(),
    }

    # Execute movement if key is in movement controls
    if key in movement_controls:
        movement_controls[key]()
    
    # Execute action if key is in action controls
    elif key in action_controls:
        action_controls[key]()
    
    # Handle numbered plan execution (0-9)
    elif ord('0') <= key <= ord('9'):
        execute_plan(key - ord('0'), robot, initial_pose)

def print_object_detection(robot):
    objects = detectObjects(robot.getCameraImage())
    print(objects)
    if objects:
        print(getObjectDistance(objects[0], robot.getFrontLidarImage()))

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

while supervisor.step(TIME_STEP) != -1:
    image = robot.getCameraImage()
    results = model(image, verbose=False)
    cv2.imshow("Camera", results[0].plot())
    if cv2.waitKey(1) == ord('q'):
        break
    if initialPose is None:
        initialPose = {
            "position": robot.getPosition(),
            "rotation": robot.getRotation()
        }
    handle_keyboard_input(keyboard.getKey(), robot, initialPose)
cv2.destroyAllWindows()
