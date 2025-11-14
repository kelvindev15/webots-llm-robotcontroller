from dataclasses import dataclass

@dataclass
class Motivation:
    subgoal: str = ""
    reasoning: str = ""
    scene_description: str = ""

@dataclass
class RobotAction:
    command: str
    parameter: float
    motivation: Motivation = Motivation()
    
    def __repr__(self):
        return f"RobotAction(command={self.command}, parameter={self.parameter}, motivation={self.motivation})"
