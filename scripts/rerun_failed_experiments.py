from concurrent.futures import Future, ThreadPoolExecutor
import threading
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


async def simulationBatch():
    # Rerun failed experiments with 429 quota exceeded errors
    import os

    failed_experiments_path = "failed_experiment.json"
    if not os.path.exists(failed_experiments_path):
        print(f"simulationBatch: failed experiments file not found at {failed_experiments_path}")
        return

    try:
        with open(failed_experiments_path, "r") as f:
            failed_experiments = json.load(f)
    except Exception as e:
        print(f"simulationBatch: Error reading failed experiments file: {e}")
        return

    # Filter experiments with 429 quota exceeded errors
    experiments_to_rerun = [
        exp for exp in failed_experiments 
        if exp.get("abortionReason") and "429" in exp.get("abortionReason", "") and exp.get("numIterations", 0) < 20
    ]

    if len(experiments_to_rerun) == 0:
        print("simulationBatch: No experiments with 429 quota errors found")
        return

    print(f"simulationBatch: Found {len(experiments_to_rerun)} experiments with 429 quota errors. Beginning reruns...")

    for index, experiment in enumerate(experiments_to_rerun):
        prompt = experiment.get("prompt")
        initial_pose = experiment.get("initialRobotPose", {}).get("pose")
        experiment_id = experiment.get("id", "unknown")
        filename = experiment.get("filename", "unknown")

        if not prompt or not initial_pose:
            print(f"simulationBatch: Skipping experiment {index} (id: {experiment_id}) - missing prompt or pose")
            continue

        print(f"simulationBatch: Rerun {index + 1}/{len(experiments_to_rerun)}")
        print(f"  Original file: {filename}")
        print(f"  ID: {experiment_id}")
        print(f"  Prompt: {prompt}")
        
        try:
            # Set the robot to the initial pose from the failed experiment
            setRobotPose(supervisor, initial_pose)
            
            # Allow a few simulation steps to stabilize sensors
            for _ in range(5):
                if supervisor.step(64) == -1:
                    print("simulationBatch: Supervisor ended while stepping to stabilize")
                    break

            # Run the LLM controller
            try:
                await llmController.ask(prompt)
                print(f"simulationBatch: Successfully completed rerun for experiment {experiment_id}")
            except Exception as e:
                print(f"simulationBatch: Error running LLM for experiment {experiment_id}: {e}")

        except Exception as e:
            print(f"simulationBatch: Unexpected error during rerun of experiment {experiment_id}: {e}")

    print("simulationBatch: Batch rerun complete")

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
    
    supervisor.step(TIME_STEP)
    pose = getRobotPose(supervisor)
    simulationKeyboardController = KeyboardController()
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
            step_counter += 1
        except Exception as e:
            robotLock.release()
            print("Error during simulation step:", e)
    cv2.destroyAllWindows()
