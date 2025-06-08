from typing import List
import json

class RobotPosition:
    def __init__(self, x: float, y: float, heading):
        self.x = x
        self.y = y
        self.heading = heading

    def __repr__(self):
        return f"RobotPosition({self.x}, {self.y}, {self.heading})"
    
class RobotTarget:
    def __init__(self, name: str, x: float, y: float, score: float = 0.0):
        self.name = name
        self.x = x
        self.y = y
        self.score = score

    def __repr__(self):
        return f"RobotTarget({self.name}, {self.x}, {self.y}, {self.score})"
    
class RobotAction:
    def __init__(self, name: str, parameter: float):
        self.name = name
        self.parameter = parameter

    def __repr__(self):
        return f"RobotAction({self.name}, {self.parameter})"

class LLMSession:
    def __init__(self, model: str, prompt: str, id: str = None):
        self.id = id
        self.model = model
        self.prompt = prompt
        self.robotPositions: List[RobotPosition] = []
        self.targets: List[str] = []
        self.scores = []
        self.actions: List[RobotAction] = []
        self.completed = False
        self.aborted = False
        self.abortionReason = None

    def addRobotPosition(self, position: RobotPosition):
        self.robotPositions.append(position)

    def setTargets(self, targets: List[str]):
        self.targets = targets

    def addScores(self, scores):
        self.scores.append(scores)

    def addAction(self, action: RobotAction):
        self.actions.append(action)

    def asObject(self):
        print(self.targets)
        return {
            "id": self.id,
            "model": self.model,
            "prompt": self.prompt,
            "robotPositions": [ {"x": pos.x, "y": pos.y, "heading": pos.heading} for pos in self.robotPositions],
            "targets": self.targets,
            "scores": self.scores,
            "actions": [ {"name": action.name, "parameters": action.parameter} for action in self.actions],
            "completed": self.completed,
            "aborted": self.aborted,
            "abortionReason": self.abortionReason
        }
    
    def toJSON(self):
        return json.dumps(self.asObject(), indent=4)
    
    def markCompleted(self):
        self.completed = True
    def markAborted(self, reason: str):
        self.aborted = True
        self.abortionReason = reason
    def isCompleted(self):
        return self.completed and not self.aborted
    def isAborted(self):
        return self.aborted
    def getAbortionReason(self):
        return self.abortionReason if self.aborted else None
    
    def __repr__(self):
        return f"LLMSession(model={self.model}, prompt={self.prompt}, robotPositions={self.robotPositions}, targets={self.targets})"
