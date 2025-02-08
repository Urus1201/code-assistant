from typing import Any, Dict, TypeVar, Generic
from abc import ABC, abstractmethod
import logging
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

StateType = TypeVar("StateType", bound=Dict[str, Any])

class BaseAgent(ABC, Generic[StateType]):
    def __init__(self, llm=None):
        self.llm = llm

    @abstractmethod
    def run(self, state: StateType) -> StateType:
        """Run the agent's main functionality with proper state management."""
        pass

    def log_error(self, error: Exception, context: str = "") -> None:
        """Log an error with optional context."""
        logger.error(f"{self.__class__.__name__} error - {context}: {str(error)}")

    def update_state(self, state: StateType, updates: Dict[str, Any]) -> StateType:
        """Safely update the state with new values."""
        return {**state, **updates}

    def add_message(self, state: StateType, message: BaseMessage) -> StateType:
        """Add a message to the state's message history."""
        messages = state.get("messages", [])
        return self.update_state(state, {"messages": messages + [message]})
