class EventManager:
    def __init__(self):
        self._observers = {}

    def subscribe(self, eventType, handler):
        if eventType not in self._observers:
            self._observers[eventType] = []
        self._observers[eventType].append(handler)

    def notify(self, eventType, data):
        for observer in self._observers[eventType]:
            observer(data)
            