from dataclasses import dataclass, field

@dataclass
class Motivation:
    subgoal: str = ""
    reasoning: str = ""
    scene_description: str = ""

@dataclass
class RobotAction:
    command: str
    parameter: float
    motivation: Motivation = field(default_factory=Motivation)
    
    def __repr__(self):
        return f"RobotAction(command={self.command}, parameter={self.parameter}, motivation={self.motivation})"
