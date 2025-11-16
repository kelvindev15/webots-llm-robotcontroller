from dataclasses import dataclass
from typing import List
import numpy as np
from common.robot.llm.RobotAction import RobotAction
from simulation import IterationData, LLMSession, RobotPose, RobotPosition, RobotStatus, RobotTarget, TargetScoringData
from simulation.events import EventType
from simulation.observers import EventManager
from controller import Supervisor
from common.utils.environment import distanceBetween, getAngleBetweenRobotAndObject, getPositionOf, getDirectionVersorOf, SceneObjects, getRobotPose, getScore

#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

@dataclass
class LLMMessage:
    message: str
    img: str = None
    
class LLMObserver():
    def __init__(self, supervisor: Supervisor, eventManager: EventManager):
        self.eventManager = eventManager
        self.supervisor = supervisor

        self.eventManager.subscribe(EventType.SIMULATION_STARTED, self.__onSimulationStarted)
        self.eventManager.subscribe(EventType.END_OF_SIMULATION, self.__onEndOfSimulation)
        self.eventManager.subscribe(EventType.SENDING_MESSAGE_TO_LLM, self.__onMessageSentToLLM)
        self.eventManager.subscribe(EventType.MESSAGE_RECEIVED_FROM_LLM, self.__onMessageReceivedFromLLM)
        self.eventManager.subscribe(EventType.LLM_INVALID_JSON_SCHEMA, self.__onInvalidJSONSchema)
        self.eventManager.subscribe(EventType.LLM_EXECUTING_ROBOT_ACTION, self.__onExecutingRobotAction)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_FAILED, self.__onActionFailed)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_ABORTED, self.__onActionAborted)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_COMPLETED, self.__onActionCompleted)
        self.eventManager.subscribe(EventType.LLM_MAX_ITERATIONS_REACHED, self.__onMaxIterationsReached)
        self.eventManager.subscribe(EventType.SIMULATION_ABORTED, self.__onAbort)
        self.eventManager.subscribe(EventType.LLM_TOO_MANY_INVALID_JSON, self.__onTooManyInvalidJSON)
        self.eventManager.subscribe(EventType.LLM_GOAL_COMPLETED, self.__onGoalCompleted)
        self.eventManager.subscribe(EventType.LLM_DANGEROUS_ACTION, self.__onDangerousAction)

        self.currentSession: LLMSession = None
        # -------------
        self.lastSentMessage: LLMMessage = None
        self.lastReceivedMessage: LLMMessage = None
        self.lastAction: RobotAction = None
        # -------------

    def __getScoringData(self):
        data = {}
        for obj in SceneObjects:
            if obj == SceneObjects.ROBOT:
                continue
            data[obj.value] = { 
                "distance": distanceBetween(self.supervisor, SceneObjects.ROBOT, obj),
                "angle": np.rad2deg(getAngleBetweenRobotAndObject(self.supervisor, obj))
            }
        return data

    def __getRobotStatus(self):
        heading = getDirectionVersorOf(self.supervisor, SceneObjects.ROBOT)
        position = getPositionOf(self.supervisor, SceneObjects.ROBOT)
        pose = RobotPose(
            position=getRobotPose(self.supervisor)["position"],
            rotation=getRobotPose(self.supervisor)["rotation"]
        )
        return RobotStatus(RobotPosition(position['x'], position['y'], heading), pose)
    
    def __addIterationData(self, actionSuccess: bool):
        iteration = IterationData(
            message=self.lastSentMessage.message if self.lastSentMessage else "",
            img=self.lastSentMessage.img if self.lastSentMessage else None,
            response=self.lastReceivedMessage.message if self.lastReceivedMessage else "",
            action=self.lastAction,
            scoringData=[
                TargetScoringData(
                    target=RobotTarget(
                        name=key, 
                        x=getPositionOf(self.supervisor, SceneObjects(key))['x'], 
                        y=getPositionOf(self.supervisor, SceneObjects(key))['y']
                ),
                    distance=value["distance"],
                    angle=value["angle"]
                ) for key, value in self.__getScoringData().items()
            ],
            endRobotStatus=self.__getRobotStatus(),
            actionSuccess=actionSuccess
        )
        self.currentSession.addIteration(iteration)
        # best-effort: persist partial session after each iteration to avoid loss
        try:
            if self.currentSession:
                self.currentSession.save(out_dir="experiments", final=False)
        except Exception:
            pass


    def __getTargetPositions(self) -> List[RobotTarget]:
        targets = []
        for obj in SceneObjects:
            if obj == SceneObjects.ROBOT:
                continue
            pos = getPositionOf(self.supervisor, obj)
            targets.append(RobotTarget(obj.value, pos['x'], pos['y']))
        return targets        

    def __onSimulationStarted(self, data: dict):
        print("LLMObserver: LLM began control", data.get("id"), data.get("prompt"), data.get("model"))
        try:
            self.currentSession = LLMSession()
            self.currentSession.setId(data.get("id"))
            self.currentSession.setPrompt(data.get("prompt"))
            self.currentSession.setSystemPrompt(data.get("system_prompt"))
            self.currentSession.setModel(data.get("model"))
            self.currentSession.setInitialRobotStatus(self.__getRobotStatus())
            self.currentSession.setTargets(self.__getTargetPositions())
        except Exception as e:
            print(f"Error during simulation start handling: {e}")
        
        try:
            if self.currentSession:
                self.currentSession.save(out_dir="experiments", final=False)
        except Exception as e:
            print(f"Error saving initial session: {e}")

    def __onMessageSentToLLM(self, data: dict):
        self.lastSentMessage = LLMMessage(message=data.get("message"), img=data.get("image"))
        print("LLMObserver: Message sent to LLM", data.get("message"))

    def __onMessageReceivedFromLLM(self, data: dict):
        print("LLMObserver: Message received from LLM", data.get("response"))
        self.lastReceivedMessage = LLMMessage(message=data.get("response"), img=data.get("image"))

    def __onInvalidJSONSchema(self, data: dict):
        print("LLMObserver: Invalid JSON schema", data)
        self.currentSession.incrementJsonErrors()

    def __onExecutingRobotAction(self, data: dict):
        print("LLMObserver: Action started", data)
        self.lastAction: RobotAction = data.get("action")

    def __onActionAborted(self, data: dict):
        print("LLMObserver: Action aborted", data)
        self.__addIterationData(actionSuccess=False)

    def __onActionCompleted(self, data: dict):
        print("LLMObserver: Action completed", data)
        self.__addIterationData(actionSuccess=True)

    def __onActionFailed(self, data: dict):
        print("LLMObserver: Action failed", data)
        self.__addIterationData(actionSuccess=False)

    def __onTooManyInvalidJSON(self, data: dict):
        print("LLMObserver: Too many invalid JSON schema responses", data)

    def __onInvalidJSONSchema(self, data: dict):
        print("LLMObserver: Invalid JSON schema", data)
        self.currentSession.incrementJsonErrors()

    def __onGoalCompleted(self, data: dict):
        print("LLMObserver: LLM goal completed", data)
        self.currentSession.goalCompleted = True
    
    def __onEndOfSimulation(self, data: dict):
        print("LLMObserver: LLM ended control", data)
        # persist final session snapshot (timestamped)
        try:
            if self.currentSession:
                self.currentSession.save(out_dir="experiments", final=True)
        except Exception:
            pass

    def __onMaxIterationsReached(self, data: dict):
        print("LLMObserver: Maximum iterations reached", data)

    def __onAbort(self, data: dict):
        print("LLMObserver: LLM control aborted", data)
        self.currentSession.simulationAborted = True
        self.currentSession.abortionReason = data.get("reason", "Unknown reason")

    def __onDangerousAction(self, data: dict):
        print("LLMObserver: Dangerous action detected", data)
        self.currentSession.incrementSafetyTriggers()   
        