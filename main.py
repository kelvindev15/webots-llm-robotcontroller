from concurrent.futures import Future, ThreadPoolExecutor
import threading
from common.llm.chats import GeminiChat, OllamaChat, OpenAIChat
from common.robot.LLMRobotController import LLMRobotController
from common.utils.environment import getRobotPose, readRobotPose, setRobotPose, setRandomRobotPose
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

async def simulationBatch():
    # Read the prompts file (prompts.txt)
    # For each prompt, reset the simulation, set the robot to a safe position, and run the LLM controller 5 times starting from that position
    # Each prompt must have 20 runs (5 positions x 4 runs each)
    # Save each session with a unique filename indicating the prompt and run number
    import os
    import random
    import math

    prompts_path = "prompts.txt"
    if not os.path.exists(prompts_path):
        print(f"simulationBatch: prompts file not found at {prompts_path}")
        return

    try:
        with open(prompts_path, "r") as f:
            prompts = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        print(f"simulationBatch: Error reading prompts file: {e}")
        return

    if len(prompts) == 0:
        print("simulationBatch: No prompts found in prompts.txt")
        return

    print(f"simulationBatch: Found {len(prompts)} prompts. Beginning batch runs...")

    # for each prompt, sample 5 safe positions and run 4 runs per position (20 runs)
    for p_index, prompt in enumerate(prompts):
        print(f"simulationBatch: Starting runs for prompt {p_index}: {prompt}")

        # gather up to 5 safe positions
        positions = []
        for i in range(5):
            pos2d = find_safe_position(supervisor)
            if pos2d is None:
                print("simulationBatch: Unable to find more safe positions; stopping position sampling")
                break
            pose = {
                "position": [pos2d[0], pos2d[1], 0.0],
                "rotation": [0, 0, 1, random.uniform(0, 2 * math.pi)]
            }
            positions.append(pose)

        if len(positions) == 0:
            print(f"simulationBatch: No safe positions for prompt {p_index}, skipping prompt")
            continue

        for pos_index, pose in enumerate(positions):
            for run_index in range(4):
                print(f"simulationBatch: Prompt {p_index} — Position {pos_index} — Run {run_index}: setting pose and starting LLM")
                try:
                    # set pose and allow a few simulation steps to stabilize sensors
                    setRobotPose(supervisor, pose)
                    for _ in range(5):
                        if supervisor.step(64) == -1:
                            print("simulationBatch: Supervisor ended while stepping to stabilize")
                            break

                    # run the LLM controller (async)
                    try:
                        await llmController.ask(prompt)
                    except Exception as e:
                        print(f"simulationBatch: Error running LLM for prompt {p_index} pos {pos_index} run {run_index}: {e}")
                except Exception as e:
                    print(f"simulationBatch: Unexpected error during run loop: {e}")

    print("simulationBatch: Batch complete")

if __name__ == "__main__":
    load_dotenv()
    executor = ThreadPoolExecutor(max_workers=4)

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
    robotChat = geminiChat
    robotChat.set_system_instruction(readSystemInstruction())
    llmController = LLMRobotController(robot, robotChat, eventManager)

    keyboard = Keyboard()
    keyboard.enable(TIME_STEP)
    image = None
    initialPose = None
    robotLock = Lock()
    simulationLock = Lock()
    # Prevent starting more than one simulation batch at a time
    batchLock = Lock()

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
    simulationKeyboardController.onKey(ord('B'), lambda: (setRobotPose(supervisor, readRobotPose()), asyncio.run(llmController.ask(readUserPrompt()))))
    simulationKeyboardController.onKey(ord('H'), lambda: print("Environment bounds:", setRandomRobotPose(supervisor)))
    # Start the full simulation batch sequentially when G is pressed. Uses batchLock to avoid parallel batches.
    def start_simulation_batch():
        # try to acquire the batch lock without blocking; if already running, ignore
        acquired = batchLock.acquire(blocking=False)
        if not acquired:
            print("start_simulation_batch: Batch already running; ignoring G press")
            return
        print("start_simulation_batch: Acquired batch lock, starting simulation batch...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(simulationBatch())
            return result
        except Exception as e:
            print(f"start_simulation_batch: Error during batch: {e}")
        
    simulationKeyboardController.onKey(ord('G'), start_simulation_batch)

    def save_session(session: LLMSession):
        # create a YYYY_MM-DD_HH-MM-SS format for the session ID
        filename = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        with open(f"experiments/experiment_{filename}.json", "w") as file:
            json.dump(session.asObject(), file, indent=4)
        print("Session saved:", session.id)


    eventManager.subscribe(EventType.SIMULATION_STARTED, lambda _: (print("LLM started"), simulationLock.acquire(blocking=False)))
    eventManager.subscribe(EventType.END_OF_SIMULATION, lambda _: (print("LLM finished"), simulationLock.release()))
    eventManager.subscribe(EventType.SIMULATION_ABORTED, lambda _: (print("LLM aborted"), simulationLock.release()))

    step_counter = 0
    initialPose = pose
    while supervisor.step(TIME_STEP) != -1:
        try:
            eventManager.notify(EventType.SIMULATION_STEP, StepEventData(step_counter))
            pressed_key = keyboard.getKey()

            try:
                simulationKeyResult = simulationKeyboardController.execute(pressed_key)
            except Exception as e:
                print("Simulation keyboard handler error:", e)
                simulationKeyResult = None

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
        except Exception as e:
            robotLock.release()
            print("Error during simulation step:", e)
    cv2.destroyAllWindows()
