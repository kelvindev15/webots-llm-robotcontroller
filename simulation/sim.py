from simulation import LLMSession, RobotPosition, RobotTarget
from simulation.events import EventType
from simulation.observers import EventManager
from controller import Supervisor
from common.utils.environment import getPositionOf, getDirectionVersorOf, SceneObjects

class LLMObserver():
    def __init__(self, supervisor: Supervisor, eventManager: EventManager):
        self.eventManager = eventManager
        self.supervisor = supervisor
        self.eventManager.subscribe(EventType.LLM_START, self.__onStart)
        self.eventManager.subscribe(EventType.LLM_FINISH, self.__onFinish)
        self.eventManager.subscribe(EventType.ABORT, self.__onAbort)
        self.eventManager.subscribe(EventType.LLM_MAX_ITERATIONS_REACHED, self.__onMaxIterationsReached)
        self.eventManager.subscribe(EventType.LLM_ACTION_COMPLETED, self.__onActionCompleted)
        self.eventManager.subscribe(EventType.LLM_ACTION_FAILED, self.__onActionFailed)
        self.currentSession = None

    def __getTargets(self):
        return list(map(lambda obj: RobotTarget(obj.name, getPositionOf(self.supervisor, obj)["x"], getPositionOf(self.supervisor, obj)["y"]), SceneObjects))

    def __recordSessionStatus(self):
        if self.currentSession is not None:
            heading = getDirectionVersorOf(self.supervisor, SceneObjects.ROBOT)
            position = getPositionOf(self.supervisor, SceneObjects.ROBOT)
            self.currentSession.addRobotPosition(RobotPosition(position['x'], position['y'], heading))
            self.currentSession.addTargets(self.__getTargets())

    def __onStart(self, data):
        print("LLMObserver: LLM began control", data)
        self.currentSession = LLMSession(data.get("model"), data.get("prompt"))
        self.__recordSessionStatus()
        
    def __onActionCompleted(self, data):
        print("LLMObserver: Action completed")
        self.__recordSessionStatus()

    def __onFinish(self, data):
        print("LLMObserver: LLM ended control")
        self.currentSession.markCompleted()
        self.eventManager.notify(EventType.LLM_SESSION_COMPLETED, self.currentSession)

    def __onActionFailed(self, data):
        print("LLMObserver: Action failed", data)
        self.eventManager.notify(EventType.ABORT, {"reason": "Action failed"})

    def __onMaxIterationsReached(self, data):
        print("LLMObserver: Maximum iterations reached")
        self.eventManager.notify(EventType.ABORT, {"reason": "Max iterations reached"})    

    def __onAbort(self, data):
        print("LLMObserver: LLM control aborted", data)
        self.currentSession.markAborted("LLM control aborted")
        self.eventManager.notify(EventType.LLM_SESSION_COMPLETED, self.currentSession)
