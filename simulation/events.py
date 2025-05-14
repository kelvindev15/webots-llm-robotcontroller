from enum import Enum
from dataclasses import dataclass

class EventType(Enum):
    SIMULATION_STEP = "simulation_step"
    SIMULATION_START = "simulation_start"
    SIMULATION_END = "simulation_end"

@dataclass
class EventData:
    """Base class for event data."""
    pass

@dataclass
class StepEventData(EventData):
    step: int
