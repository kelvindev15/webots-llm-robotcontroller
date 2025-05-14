from simulation.events import EventType, EventData
from typing import Callable

class EventManager:
    def __init__(self):
        self._observers = {}

    def subscribe(self, eventType: EventType, handler: Callable[[EventData], None]):
        if eventType not in self._observers:
            self._observers[eventType] = []
        self._observers[eventType].append(handler)

    def unsubscribe(self, handler: Callable[[EventData], None]):
        for _, observers in self._observers.items():
            if handler in observers:
                observers.remove(handler)
                break

    def notify(self, eventType: EventType, data: EventData):
        for observer in self._observers[eventType]:
            observer(data)
            