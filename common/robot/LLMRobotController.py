import uuid
from common.llm.chats import LLMChat
from common.utils.images import toBase64Image
from common.utils.robot import getDistancesFromLidar, getDistanceDescription
from common.robot.RobotController import RobotController
from common.robot.llm.LLMPlan import LLMPlan
from common.robot.llm.ActionAdapter import ActionAdapter
from common.robot.llm.LLMAdapter import LLMAdapter
from controllers.webots.pr2.PR2Controller import PR2Controller

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
        self.actionLock.acquire()
        chat_id = str(uuid.uuid4())
        self.llmAdapter.clear()
        self.chat.set_chat_id(chat_id)

        action = await self.llmAdapter.iterate(prompt, toBase64Image(self.robot.getCameraImage()))
        while action.command != "COMPLETE":
            success = await self.actionAdapter.execute(action)
            if not success:
                self.actionLock.release()
                return
            action = await self.llmAdapter.iterate(self.__buildSceneDescription(), toBase64Image(self.robot.getCameraImage()))
        self.actionLock.release()
    