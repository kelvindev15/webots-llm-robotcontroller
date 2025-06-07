from dataclasses import dataclass

@dataclass
class RobotAction:
    command: str
    parameter: float

    def __repr__(self):
        return f"RobotAction(command={self.command}, parameter={self.parameter})"
