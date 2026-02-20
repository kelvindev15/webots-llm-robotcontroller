import asyncio
import uuid
from common.llm.chats import LLMChat
from common.robot.llm import LLMResult
from common.utils.images import toBase64Image
from common.utils.robot import getDistancesFromLidar, getDistanceDescription
from common.robot.RobotController import RobotController
from common.robot.llm.ActionAdapter import ActionAdapter, ActionStatus
from common.robot.llm.LLMAdapter import LLMAdapter
from controllers.webots.pr2.PR2Controller import PR2Controller

from simulation.events import EventType
from simulation.observers import EventManager
from threading import Lock
from dataclasses import dataclass

@dataclass
class CorrectiveLoopResult:
    success: bool
    iterationCount: int = 0

class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat, eventManager: EventManager = None):
        self.robot = robotController
        self.chat = chat
        self.llmAdapter = LLMAdapter(chat)
        self.actionAdapter = ActionAdapter(robotController)
        self.eventManager = eventManager
        self.sessionLock = Lock()

    def __buildSceneDescription(self, prompt = None) -> str:
        preamble = f"Goal: {prompt}" if prompt is not None else "Here is the current view of the robot."
        view_description = f"""
                {preamble}
                {getDistanceDescription(getDistancesFromLidar(self.robot.getFrontLidarImage(), 90, 8))}
                """.strip()
        return view_description if isinstance(self.robot, PR2Controller) else "Current view:"
        
    async def ask(self, prompt: str, maxIterations: int = 30):
        controlAcquired = self.sessionLock.acquire(blocking=False)
        if controlAcquired:
            chat_id = str(uuid.uuid4())
            self.llmAdapter.clear()
            self.chat.set_chat_id(chat_id)
            self.eventManager.notify(EventType.SIMULATION_STARTED, { "model": self.chat.model_name, "prompt": prompt, "id": chat_id, "system_prompt": self.chat.get_system_instruction() })
            iterations = 0
            try:
                self.eventManager.notify(EventType.SENDING_MESSAGE_TO_LLM, { "message": prompt, "img": toBase64Image(self.robot.getCameraImage()) })
                response = await self.llmAdapter.iterate(self.__buildSceneDescription(prompt), toBase64Image(self.robot.getCameraImage()))
                self.eventManager.notify(EventType.MESSAGE_RECEIVED_FROM_LLM, { "response": response })
                while iterations < maxIterations and not(response.ok and response.value.command == "COMPLETE"):
                    iterations += 1
                    print(f"LLMRobotController: Iteration {iterations} of {maxIterations}")
                    if response.ok and self.actionAdapter.checkSafety(response.value, self.robot.getLidarImage(30, 0)): # robot action
                        self.eventManager.notify(EventType.LLM_EXECUTING_ROBOT_ACTION, { "action": response.value })
                        try:
                            actionTask = asyncio.create_task(self.actionAdapter.execute(response.value))
                            await asyncio.wait_for(actionTask, 30)
                        except asyncio.TimeoutError:
                            self.eventManager.notify(EventType.LLM_ROBOT_ACTION_ABORTED, { "action": response.value, "reason": "Action execution timed out." })
                            break

                        actionResult = await actionTask
                        if actionResult.status == ActionStatus.SUCCESS:
                            self.eventManager.notify(EventType.LLM_ROBOT_ACTION_COMPLETED, { "action": response.value })
                            self.eventManager.notify(EventType.SENDING_MESSAGE_TO_LLM, { "message": self.__buildSceneDescription(), "img": toBase64Image(self.robot.getCameraImage()) })
                            response = await self.llmAdapter.iterate(self.__buildSceneDescription(prompt), toBase64Image(self.robot.getCameraImage()))
                            self.eventManager.notify(EventType.MESSAGE_RECEIVED_FROM_LLM, { "response": response })
                        else:
                            self.eventManager.notify(EventType.LLM_ROBOT_ACTION_FAILED, { "action": response.value, "reason": actionResult.message })
                            break
                    elif response.ok:
                        self.eventManager.notify(EventType.LLM_DANGEROUS_ACTION, { "action": response.value })
                        message = f"The action: {response.value.command} with parameter {response.value.parameter} is considered dangerous as it may lead to a collision. Please provide a different action that is safe to execute."
                        self.eventManager.notify(EventType.SENDING_MESSAGE_TO_LLM, { "message": message, "img": toBase64Image(self.robot.getCameraImage()) })
                        response = await self.llmAdapter.iterate(self.__buildSceneDescription(f"{prompt}\n{message}"), toBase64Image(self.robot.getCameraImage()))
                        self.eventManager.notify(EventType.MESSAGE_RECEIVED_FROM_LLM, { "response": response })
                    elif not response.ok:
                        self.eventManager.notify(EventType.LLM_INVALID_JSON_SCHEMA, {})
                        message = f"The JSON you provided is invalid. Please respond again following the correct schema\nExpected Schema: {self.llmAdapter.responseSchema}\nReceived: {response.error}\n"
                        self.eventManager.notify(EventType.SENDING_MESSAGE_TO_LLM, { "message": message, "img": toBase64Image(self.robot.getCameraImage()) })
                        response = await self.llmAdapter.iterate(self.__buildSceneDescription(f"{prompt}\n{message}"), toBase64Image(self.robot.getCameraImage()), None)
                        self.eventManager.notify(EventType.MESSAGE_RECEIVED_FROM_LLM, { "response": response })
                if iterations >= maxIterations:
                    self.eventManager.notify(EventType.LLM_MAX_ITERATIONS_REACHED, { "max_iterations": maxIterations })
                elif response.ok and response.value.command == "COMPLETE":
                    self.eventManager.notify(EventType.LLM_GOAL_COMPLETED, { "goal": prompt })
                
                if not(response.ok):
                    self.eventManager.notify(EventType.SIMULATION_ABORTED, { "reason": "LLM failed to provide valid responses." })    
                elif iterations >= maxIterations:
                    self.eventManager.notify(EventType.SIMULATION_ABORTED, { "reason": "Maximum iterations reached without completing the goal." })
                elif response.ok and response.value.command != "COMPLETE":
                    self.eventManager.notify(EventType.SIMULATION_ABORTED, { "reason": "Error occured while performing actions before completion." })        
            except Exception as e:
                print("Error in LLMRobotController.ask:", e)
                self.eventManager.notify(EventType.SIMULATION_ABORTED, { "reason": str(e) })       
            finally:
                # always release the lock and notify finish
                self.sessionLock.release()
                self.eventManager.notify(EventType.END_OF_SIMULATION, {})
        else:
            print("LLMRobotController: Unable to acquire action lock, another session is in progress.")
    