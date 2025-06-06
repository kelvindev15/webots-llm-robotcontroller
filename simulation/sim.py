from simulation.events import EventType
from simulation.observers import EventManager

class LLMObserver():
    def __init__(self, eventManager: EventManager):
        self.eventManager = eventManager
        self.eventManager.subscribe(EventType.LLM_START, self.__onStart)
        self.eventManager.subscribe(EventType.LLM_FINISH, self.__onFinish)
        self.eventManager.subscribe(EventType.ABORT, self.__onAbort)
        self.eventManager.subscribe(EventType.LLM_MAX_ITERATIONS_REACHED, self.__onMaxIterationsReached)
        self.eventManager.subscribe(EventType.LLM_ACTION_COMPLETED, self.__onActionCompleted)
        self.eventManager.subscribe(EventType.LLM_ACTION_FAILED, self.__onActionFailed)

    def __onStart(self, data):
        print("LLMObserver: LLM began control", data)
        # Add any additional logic needed when the simulation starts

    def __onFinish(self, data):
        print("LLMObserver: LLM ended control")
        # Add any additional logic needed when the simulation stops

    def __onMaxIterationsReached(self, data):
        print("LLMObserver: Maximum iterations reached")
        self.eventManager.notify(EventType.ABORT, {"reason": "Max iterations reached"})

    def __onActionCompleted(self, data):
        print("LLMObserver: Action completed")
        # Add any additional logic needed when an action is completed

    def __onActionFailed(self, data):
        print("LLMObserver: Action failed", data)
        # Add any additional logic needed when an action fails

    def __onAbort(self, data):
        print("LLMObserver: LLM control aborted", data)
        # Add any additional logic needed when the LLM control is aborted
