from dataclasses import dataclass

@dataclass
class RobotAction:
    command: str
    parameter: float
