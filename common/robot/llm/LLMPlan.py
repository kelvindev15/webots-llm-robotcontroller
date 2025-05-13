from dataclasses import dataclass
from typing import List
from common.robot.llm.RobotAction import RobotAction

@dataclass
class LLMPlan():
    goal: str
    actions: List[RobotAction]
