from dataclasses import dataclass
import uuid
from common.llm.chats import LLMChat
from common.utils.images import toBase64Image
from common.utils.robot import getDistancesFromLidar, getDistanceDescription
from common.robot.RobotController import RobotController
from common.robot.llm.LLMPlan import LLMPlan
from common.robot.llm.ActionAdapter import ActionAdapter
from common.robot.llm.LLMAdapter import LLMAdapter
from controllers.webots.pr2.PR2Controller import PR2Controller

from simulation.events import EventType
from simulation.observers import EventManager

class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat, eventManager: EventManager = None):
        self.robot = robotController
        self.chat = chat
        self.llmAdapter = LLMAdapter(chat)
        self.actionAdapter = ActionAdapter(robotController)
        self.locked = False
        self.eventManager = eventManager
        self.abort = False
        if self.eventManager is not None:
            self.eventManager.subscribe(EventType.ABORT, self.__onAbort)

    def __buildSceneDescription(self) -> str:
        view_description = f"""
                Here is the current view of the robot.
                {getDistanceDescription(getDistancesFromLidar(self.robot.getFrontLidarImage(), 90))}
                """.strip()
        return view_description if isinstance(self.robot, PR2Controller) else "Current view:"
    
    def __onAbort(self, _):
        self.locked = False
        self.abort = True

    def __completeSession(self):
        if self.locked:
            self.locked = False
            self.eventManager.notify(EventType.LLM_FINISH, {"success": True})

    def ask(self, prompt: str, maxIterations: int = 30) -> LLMPlan:
        if self.locked and not self.abort:
            print("LLMRobotController: LLM is already running, cannot start a new session.")
            return None
        self.locked = True
        self.abort = False
        chat_id = str(uuid.uuid4())
        self.eventManager.notify(EventType.LLM_START, {"model": self.chat.model_name, "prompt": prompt, "experiment_id": chat_id})
        self.llmAdapter.clear()
        self.chat.set_chat_id(chat_id)
        iteration_count = 0
        def handler(prompt: str, action=None):
            nonlocal iteration_count
            if iteration_count > 0:
                self.eventManager.notify(EventType.LLM_ACTION_COMPLETED, {"action": action})
            if self.abort:
                self.abort = False
                return
            elif iteration_count >= maxIterations:
                self.locked = False
                self.eventManager.notify(EventType.LLM_MAX_ITERATIONS_REACHED, {"iterations": iteration_count})
                return
            
            iteration_count += 1
            action = self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
            if action.command != "COMPLETE":
                success = self.actionAdapter.execute(action, lambda: handler(self.__buildSceneDescription(), action))
                if not success:
                    self.locked = False
                    self.eventManager.notify(EventType.LLM_ACTION_FAILED, {"action": action})
                    return
            else:
                self.__completeSession()
                return
        handler(prompt)
    