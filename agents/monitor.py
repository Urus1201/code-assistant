import logging
from typing import Dict, Any
from .base_agent import BaseAgent
from langchain_core.messages import AIMessage  # Import AIMessage

logger = logging.getLogger(__name__)

class MonitorAgent(BaseAgent):
    def __init__(self, llm):
        self.llm = llm

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            log = state["errors"][-1] if state["errors"] else ""
            recommendation = self.analyze_log(log)
            state = self.add_message(
                state,
                AIMessage(content=f"Monitor recommendation: {recommendation}")
            )
            if recommendation != "no_error":
                return self.update_state(state, {
                    "status": "retry",
                    "next": "executor"
                })
            else:
                return self.update_state(state, {
                    "status": "completed"
                })
        except Exception as e:
            self.log_error(e, "log analysis")
            return self.update_state(state, {
                "status": "error",
                "errors": state.get("errors", []) + [str(e)]
            })

    def analyze_log(self, log: str) -> str:
        """
        Analyzes the log and recommends the next step.
        Returns a command or action to take.
        """
        log_lower = log.lower()
        if "error" in log_lower or "exception" in log_lower:
            logger.warning("Error detected in log.")
            # More specific recommendations:
            if "modulenotfounderror" in log_lower:
                module_name = log.split("No module named '")[-1].split("'")[0]
                return f"install_module:{module_name}"  # Install missing module
            elif "filenotfounderror" in log_lower:
                file_path = log.split("No such file or directory: '")[-1].split("'")[0]
                return f"check_file_path:{file_path}"  # Check file path
            elif "nameerror" in log_lower:
                return "fix_code:undefined_variable"  # Fix undefined variable
            else:
                return "fix_code:general_error"  # General code error
        else:
            return "no_error"