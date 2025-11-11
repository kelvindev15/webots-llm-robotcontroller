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
from threading import Lock

class LLMRobotController:

    def __init__(self, robotController: RobotController, chat: LLMChat, eventManager: EventManager = None):
        self.robot = robotController
        self.chat = chat
        self.llmAdapter = LLMAdapter(chat)
        self.actionAdapter = ActionAdapter(robotController)
        self.eventManager = eventManager
        self.abort = False

        self.actionLock = Lock()

    def __buildSceneDescription(self) -> str:
        view_description = f"""
                Here is the current view of the robot.
                {getDistanceDescription(getDistancesFromLidar(self.robot.getFrontLidarImage(), 90))}
                """.strip()
        return view_description if isinstance(self.robot, PR2Controller) else "Current view:"

    async def ask(self, prompt: str, maxIterations: int = 30) -> LLMPlan:
        controlAcquired = self.actionLock.acquire(blocking=False)
        if controlAcquired:
            self.eventManager.notify(EventType.LLM_START, { "prompt": prompt, "model": self.chat.model_name, "experiment_id": str(uuid.uuid4()) })
            chat_id = str(uuid.uuid4())
            self.llmAdapter.clear()
            self.chat.set_chat_id(chat_id)

            iteration = 0
            action = await self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
            while action.command != "COMPLETE":
                success = await self.actionAdapter.execute(action)
                iteration += 1
                if not success:
                    self.eventManager.notify(EventType.LLM_ACTION_FAILED, { "action": action })
                    self.actionLock.release()
                    return
                else:
                    self.eventManager.notify(EventType.LLM_ACTION_COMPLETED, { "action": action })
                if iteration >= maxIterations:
                    self.eventManager.notify(EventType.LLM_MAX_ITERATIONS_REACHED, { "max_iterations": maxIterations })
                    self.actionLock.release()
                    return
                action = await self.llmAdapter.iterate(self.__buildSceneDescription(), toBase64Image(self.robot.getCameraImage()))
            self.actionLock.release()
            self.eventManager.notify(EventType.LLM_FINISH, {})
        else:
            print("LLMRobotController: Unable to acquire action lock, another session is in progress.")
    