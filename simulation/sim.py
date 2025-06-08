import numpy as np
from common.robot.llm.RobotAction import RobotAction as Action
from simulation import LLMSession, RobotAction, RobotPosition, RobotTarget
from simulation.events import EventType
from simulation.observers import EventManager
from controller import Supervisor
from common.utils.environment import distanceBetween, getAngleBetweenRobotAndObject, getPositionOf, getDirectionVersorOf, SceneObjects, getScore

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
        self.currentSession = LLMSession(data.get("model"), data.get("prompt"), id=data.get("experiment_id"))
        self.currentSession.setTargets(list(map(lambda x: x.value, SceneObjects)))
        self.__recordSessionStatus()
        
    def __onActionCompleted(self, data):
        action: Action = data.get("action")
        print("LLMObserver: Action completed", data)
        self.__recordSessionStatus()
        self.currentSession.addAction(RobotAction(action.command, action.parameter))

    def __onFinish(self, data):
        print("LLMObserver: LLM ended control")
        self.currentSession.markCompleted()
        self.eventManager.notify(EventType.LLM_SESSION_COMPLETED, self.currentSession)

    def __onActionFailed(self, data):
        print("LLMObserver: Action failed", data)
        self.eventManager.notify(EventType.ABORT, {"reason": f"Action {data} failed"})

    def __onMaxIterationsReached(self, data):
        print("LLMObserver: Maximum iterations reached")
        self.eventManager.notify(EventType.ABORT, {"reason": f"Max iterations reached ({data.get('iterations', 'Unknown')})"})

    def __onAbort(self, data):
        print("LLMObserver: LLM control aborted", data)
        self.currentSession.markAborted(data.get("reason", "Unknown reason"))
        self.eventManager.notify(EventType.LLM_SESSION_COMPLETED, self.currentSession)
