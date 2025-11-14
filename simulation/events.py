from enum import Enum
from dataclasses import dataclass

class EventType(Enum):
    SIMULATION_STARTED = "simulation_start"
    SIMULATION_ABORTED = "abort"
    END_OF_SIMULATION = "simulation_end"

    SENDING_MESSAGE_TO_LLM = "message_sent_to_llm"
    MESSAGE_RECEIVED_FROM_LLM = "message_received_from_llm"
    LLM_RESPONSE_TIMEOUT = "llm_response_timeout"
    LLM_RATE_LIMIT_EXCEEDED = "llm_rate_limit_exceeded"
    LLM_INVALID_JSON_SCHEMA = "llm_invalid_json_schema"
    LLM_INVALID_ROBOT_ACTION = "llm_invalid_robot_action"

    LLM_EXECUTING_ROBOT_ACTION = "llm_robot_action_started"
    LLM_ROBOT_ACTION_FAILED = "llm_robot_action_failed"
    LLM_ROBOT_ACTION_COMPLETED = "llm_robot_action_completed"
    LLM_ROBOT_ACTION_ABORTED = "llm_robot_action_aborted"
    LLM_DANGEROUS_ACTION = "llm_dangerous_action"

    LLM_MAX_ITERATIONS_REACHED = "llm_max_iterations_reached"
    LLM_TOO_MANY_INVALID_JSON = "llm_too_many_invalid_json"
    LLM_TOO_MANY_DANGEROUS_ACTIONS = "llm_too_many_dangerous_actions"
    
    LLM_GOAL_COMPLETED = "llm_goal_completed"
    
    # remove this....
    LLM_START = "llm_start"
    LLM_FINISH = "llm_finish"
    #----------------------------------
    
    SIMULATION_STEP = "simulation_step"

@dataclass
class EventData:
    """Base class for event data."""
    pass

@dataclass
class StepEventData(EventData):
    step: int
