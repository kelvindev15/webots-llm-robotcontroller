from enum import Enum
from dataclasses import dataclass

class EventType(Enum):
    SIMULATION_STEP = "simulation_step"
    SIMULATION_START = "simulation_start"
    SIMULATION_END = "simulation_end"
    LLM_START = "llm_start"
    LLM_FINISH = "llm_finish"
    LLM_ACTION_COMPLETED = "llm_action_completed"
    LLM_ACTION_FAILED = "llm_action_failed"
    LLM_MAX_ITERATIONS_REACHED = "llm_max_iterations_reached"
    ABORT = "abort"

@dataclass
class EventData:
    """Base class for event data."""
    pass

@dataclass
class StepEventData(EventData):
    step: int
