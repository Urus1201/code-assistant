from typing import TypedDict, List, Literal, Optional, Dict, Any, Union
from enum import Enum

class ActionType(str, Enum):
    CREATE_DIR = "create_directory"
    CREATE_FILE = "create_file"
    CREATE_VENV = "create_virtual_environment"
    INSTALL_DEPS = "install_dependencies"
    RUN_COMMAND = "run_command"
    CUSTOM = "custom_action"

class ValidationResult(TypedDict):
    success: bool
    message: str
    details: Optional[Dict[str, Any]]

class StepValidation(TypedDict):
    type: str  # file_exists, command_output, custom
    criteria: Union[str, List[str]]
    expected_result: Any

class ActionResult(TypedDict):
    success: bool
    output: Optional[str]
    error: Optional[str]
    validation: ValidationResult

class Action(TypedDict):
    id: str
    type: ActionType
    params: dict
    description: str
    validation: Optional[StepValidation]
    dependencies: List[str]  # IDs of actions this depends on
    result: Optional[ActionResult]

class Plan(TypedDict):
    objective: str
    actions: List[Action]
    context: Dict[str, Any]  # Shared context between agents
    dependencies: List[str]
    estimated_time: str
    requirements: List[str]
    status: str  # planning, executing, completed, failed
    current_step: Optional[str]  # ID of current action
