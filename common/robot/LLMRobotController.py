from dataclasses import dataclass
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
                An 'inf' value for distance means that no object is in the range of the LIDAR beam.
                Object may still be present, but they are either too far away or not captured by that specific beam.
                So move carefully!
                """.strip()
        return view_description if isinstance(self.robot, PR2Controller) else "Current view:"
    
    def __onAbort(self, event_data):
        self.abort = True

    def __complete(self):
        if self.locked:
            self.locked = False
            self.eventManager.notify(EventType.LLM_FINISH, {"prompt": "LLM control completed"})

    def ask(self, prompt: str, maxIterations: int = 20) -> LLMPlan:
        self.abort = False
        if self.locked:
            return None
        self.locked = True
        self.eventManager.notify(EventType.LLM_START, {"model": self.chat.model_name, "prompt": prompt})
        self.llmAdapter.clear()
        iteration_count = 0
        def handler(prompt: str):
            nonlocal iteration_count
            if iteration_count > 0:
                # TODO: add action to parameters
                self.eventManager.notify(EventType.LLM_ACTION_COMPLETED, {"prompt": prompt})
            if self.abort:
                self.locked = False
                return
            elif iteration_count >= maxIterations:
                # TODO: add correct reason to parameters
                self.eventManager.notify(EventType.LLM_MAX_ITERATIONS_REACHED, {"prompt": prompt})
                self.locked = False
                return
            
            iteration_count += 1
            action = self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
            if action.command != "COMPLETE":
                success = self.actionAdapter.execute(action, lambda: handler(self.__buildSceneDescription()))
                if not success:
                    self.eventManager.notify(EventType.LLM_ACTION_FAILED, {"action": action})
                    self.locked = False
                    return
            else:
                self.__complete()
                return
        handler(prompt)
    