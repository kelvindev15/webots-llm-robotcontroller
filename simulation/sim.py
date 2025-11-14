import numpy as np
from simulation import RobotPosition
from simulation.events import EventType
from simulation.observers import EventManager
from controller import Supervisor
from common.utils.environment import distanceBetween, getAngleBetweenRobotAndObject, getPositionOf, getDirectionVersorOf, SceneObjects, getScore

#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

class LLMObserver():
    def __init__(self, supervisor: Supervisor, eventManager: EventManager):
        self.eventManager = eventManager
        self.supervisor = supervisor

        self.eventManager.subscribe(EventType.SIMULATION_STARTED, self.__onStart)
        self.eventManager.subscribe(EventType.END_OF_SIMULATION, self.__onCompleted)
        self.eventManager.subscribe(EventType.SENDING_MESSAGE_TO_LLM, self.__onMessageSentToLLM)
        self.eventManager.subscribe(EventType.MESSAGE_RECEIVED_FROM_LLM, self.__onMessageReceivedFromLLM)
        self.eventManager.subscribe(EventType.LLM_INVALID_JSON_SCHEMA, self.__onInvalidJSONSchema)
        self.eventManager.subscribe(EventType.LLM_EXECUTING_ROBOT_ACTION, self.__onActionStarted)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_FAILED, self.__onActionFailed)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_ABORTED, self.__onActionAborted)
        self.eventManager.subscribe(EventType.LLM_ROBOT_ACTION_COMPLETED, self.__onActionCompleted)
        self.eventManager.subscribe(EventType.LLM_MAX_ITERATIONS_REACHED, self.__onMaxIterationsReached)
        self.eventManager.subscribe(EventType.SIMULATION_ABORTED, self.__onAbort)
        self.eventManager.subscribe(EventType.LLM_TOO_MANY_INVALID_JSON, self.__onTooManyInvalidJSON)
        self.eventManager.subscribe(EventType.LLM_GOAL_COMPLETED, self.__onCompleted)
        self.eventManager.subscribe(EventType.LLM_DANGEROUS_ACTION, self.__onDangerousAction)

        self.currentSession = None

    def __getScores(self):
        scores = {}
        for obj in SceneObjects:
            if obj == SceneObjects.ROBOT:
                continue
            scores[obj.value] = { 
                "score": getScore(self.supervisor, obj),
                "distance": distanceBetween(self.supervisor, SceneObjects.ROBOT, obj),
                "angle": np.rad2deg(getAngleBetweenRobotAndObject(self.supervisor, obj))
            }
        return scores

    def __recordSessionStatus(self):
        if self.currentSession is not None:
            heading = getDirectionVersorOf(self.supervisor, SceneObjects.ROBOT)
            position = getPositionOf(self.supervisor, SceneObjects.ROBOT)
            self.currentSession.addRobotPosition(RobotPosition(position['x'], position['y'], heading))
            self.currentSession.addScores(self.__getScores())

    def __onStart(self, data):
        print("LLMObserver: LLM began control", data)
        #self.currentSession = LLMSession(data.get("model"), data.get("prompt"), id=data.get("experiment_id"))
        #self.currentSession.setTargets(list(map(lambda x: x.value, SceneObjects)))
        #self.__recordSessionStatus()

    def __onMessageSentToLLM(self, data):
        print("LLMObserver: Message sent to LLM", data)

    def __onMessageReceivedFromLLM(self, data):
        print("LLMObserver: Message received from LLM", data)

    def __onInvalidJSONSchema(self, data):
        print("LLMObserver: Invalid JSON schema", data)

    def __onActionStarted(self, data):
        print("LLMObserver: Action started", data)

    def __onActionAborted(self, data):
        print("LLMObserver: Action aborted", data)

    def __onActionCompleted(self, data):
        #action: Action = data.get("action")
        print("LLMObserver: Action completed", data)
        # self.__recordSessionStatus()
        # self.currentSession.addAction(RobotAction(action.command, action.parameter))

    def __onTooManyInvalidJSON(self, data):
        print("LLMObserver: Too many invalid JSON schema responses", data)

    def __onInvalidJSONSchema(self, data):
        print("LLMObserver: Invalid JSON schema", data)

    def __onCompleted(self, data):
        print("LLMObserver: LLM ended control", data)
        # self.currentSession.markCompleted()
        # self.eventManager.notify(EventType.LLM_GOAL_COMPLETED, self.currentSession)

    def __onActionFailed(self, data):
        print("LLMObserver: Action failed", data)
        

    def __onMaxIterationsReached(self, data):
        print("LLMObserver: Maximum iterations reached", data)


    def __onAbort(self, data):
        print("LLMObserver: LLM control aborted", data)
        # self.currentSession.markAborted(data.get("reason", "Unknown reason"))

    def __onDangerousAction(self, data):
        print("LLMObserver: Dangerous action detected", data)    
        
