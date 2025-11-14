from concurrent.futures import Future
from common.llm.chats import GeminiChat, OllamaChat, OpenAIChat
from common.robot.LLMRobotController import LLMRobotController
from common.utils.environment import getRobotPose, setRobotPose, setRandomRobotPose
from common.utils.geometry import find_safe_position
from controllers.webots.pr2.PR2Controller import PR2Controller
from controllers.webots.pr2.devices import PR2Devices
from controllers.webots.keyboard import KeyboardController
from controller import Keyboard, Supervisor
from common.utils.robot import readSystemInstruction, readUserPrompt
from dotenv import load_dotenv
from simulation import LLMSession
from simulation.observers import EventManager
from simulation.events import EventType, StepEventData
import cv2
import json
import datetime
from simulation.sim import LLMObserver
import asyncio
from threading import Lock

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

if __name__ == "__main__":
    load_dotenv()

    TIME_STEP = 64
    MAX_SPEED = 6.28
    eventManager = EventManager()
    supervisor = Supervisor()
    llmObserver = LLMObserver(supervisor, eventManager)
    pr2Devices = PR2Devices(supervisor, eventManager, TIME_STEP)
    # khepheraDevices = KhepheraDevices(supervisor, eventManager, TIME_STEP)
    robot = PR2Controller(pr2Devices, eventManager)
    # robot = KhepheraController(khepheraDevices, eventManager)
    geminiChat = GeminiChat()
    ollamaChat = OllamaChat(model_name="gemma3:4b")
    openaiChat = OpenAIChat(model_name="gpt-4o-mini")
    robotChat = openaiChat
    robotChat.set_system_instruction(readSystemInstruction())
    llmController = LLMRobotController(robot, robotChat, eventManager)

    keyboard = Keyboard()
    keyboard.enable(TIME_STEP)
    image = None
    initialPose = None
    robotLock = Lock()
    simulationLock = Lock()

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

    supervisor.step(TIME_STEP)
    pose = getRobotPose(supervisor)
    simulationKeyboardController = KeyboardController()
    simulationKeyboardController.onKey(ord('P'), lambda: asyncio.run(llmController.ask(readUserPrompt())))
    simulationKeyboardController.onKey(ord('L'), lambda: print("Front Lidar:", robot.getFrontLidarImage()))
    simulationKeyboardController.onKey(ord('B'), lambda: (setRobotPose(supervisor, pose), llmController.ask(readUserPrompt())))
    simulationKeyboardController.onKey(ord('H'), lambda: print("Environment bounds:", setRandomRobotPose(supervisor)))

    def save_session(session: LLMSession):
        # create a YYYY_MM-DD_HH-MM-SS format for the session ID
        filename = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        with open(f"experiments/experiment_{filename}.json", "w") as file:
            json.dump(session.asObject(), file, indent=4)
        print("Session saved:", session.id)


    eventManager.subscribe(EventType.LLM_GOAL_COMPLETED, save_session)
    eventManager.subscribe(EventType.SIMULATION_STARTED, lambda _: (print("LLM started"), simulationLock.acquire(blocking=False)))
    eventManager.subscribe(EventType.END_OF_SIMULATION, lambda _: (print("LLM finished"), simulationLock.release()))
    eventManager.subscribe(EventType.SIMULATION_ABORTED, lambda _: (print("LLM aborted"), simulationLock.release()))

    step_counter = 0
    initialPose = pose
    while supervisor.step(TIME_STEP) != -1:
        eventManager.notify(EventType.SIMULATION_STEP, StepEventData(step_counter))
        pressed_key = keyboard.getKey()
        simulationKeyboardController.execute(pressed_key)

        lock_acquired = robotLock.acquire(blocking=False)
        if lock_acquired:
            try:
                keyboard_result = robotKeyboardController.execute(pressed_key)
            except Exception as e:
                robotLock.release()
                print("Keyboard handler error:", e)
                keyboard_result = None

            if isinstance(keyboard_result, Future):
                keyboard_result.add_done_callback(lambda _f: robotLock.release())
            else:
                robotLock.release()

            if keyboard_result is False and not simulationLock.locked():
                robot.stop()

        # reuse pressed_key instead of calling getKey() again
        handle_keyboard_input(pressed_key, robot, initialPose)
        step_counter += 1
    cv2.destroyAllWindows()
