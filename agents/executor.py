from pathlib import Path
import subprocess
from typing import Dict, Any, Optional
from .types import Plan, Action, ActionType, ActionResult, ValidationResult
import logging

logger = logging.getLogger(__name__)

class ExecutorAgent:
    def __init__(self, llm):
        self.llm = llm
        self.action_handlers = {
            ActionType.CREATE_DIR: self._handle_create_dir,
            ActionType.CREATE_FILE: self._handle_create_file,
            ActionType.CREATE_VENV: self._handle_create_venv,
            ActionType.INSTALL_DEPS: self._handle_install_deps,
            ActionType.RUN_COMMAND: self._handle_run_command,
            ActionType.CUSTOM: self._handle_custom_action
        }

    def execute_plan(self, state: Dict[str, Any]) -> Dict[str, Any]:
        plan: Plan = state["plan"]
        context = plan["context"]
        
        # import pdb; pdb.set_trace()
        while True:
            current_action = self._get_next_action(plan)
            if not current_action:
                break  # No more pending actions

            try:
                result = self._execute_action(current_action, context)
                validation = self._validate_action(current_action, result)
                
                current_action["result"] = {
                    "success": validation["success"],
                    "output": result.get("output"),
                    "error": result.get("error"),
                    "validation": validation
                }
                
                context.update(self._extract_context_updates(current_action))
            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                state.setdefault("errors", []).append(str(e))
                return self.update_state(state, {
                    "status": "error",
                    "next": "monitoring"
                })
        
        return self.update_state(state, {
            "plan": plan,
            "context": context,
            "status": "completed",
            "next": "reviewer"
        })

    def _get_next_action(self, plan: Plan) -> Optional[Action]:
        """Find next action where all dependencies are completed successfully"""
        for action in plan["actions"]:
            if not action.get("result"):  # Not executed yet
                dependencies_met = all(
                    self._is_action_completed(plan, dep_id)
                    for dep_id in action.get("dependencies", [])
                )
                if dependencies_met:
                    return action
        return None

    def _is_action_completed(self, plan: Plan, action_id: str) -> bool:
        """Check if an action completed successfully"""
        for action in plan["actions"]:
            if action["id"] == action_id:
                result = action.get("result")
                return result and result["success"]
        return False

    def _extract_context_updates(self, action: Action) -> Dict[str, Any]:
        """Extract relevant information from action result to update context"""
        result = action.get("result")
        if not result or not result["success"]:
            return {}
            
        updates = {}
        if action["type"] == ActionType.CREATE_DIR:
            updates["last_created_dir"] = action["params"]["path"]
        elif action["type"] == ActionType.CREATE_FILE:
            updates["last_created_file"] = action["params"]["path"]
        # Add more context updates based on action types...
        
        return updates

    def _execute_action(self, action: Action, context: Dict[str, Any]) -> ActionResult:
        handler = self.action_handlers.get(ActionType(action["type"]))
        if handler:
            return handler(action["params"])
        raise ValueError(f"Unknown action type: {action['type']}")

    def _validate_action(self, action: Action, result: ActionResult) -> ValidationResult:
        if not action.get("validation"):
            return {"success": True}
            
        validation = action["validation"]
        if validation["type"] == "file_exists":
            success = Path(validation["criteria"]).exists()
        elif validation["type"] == "command_output":
            try:
                subprocess.run(
                    validation["criteria"],
                    shell=True,
                    check=True,
                    capture_output=True
                )
                success = True
            except subprocess.CalledProcessError:
                success = False
        else:
            success = False
        
        return {"success": success, "message": validation.get("message", "")}

    def _handle_create_dir(self, params: dict) -> ActionResult:
        path = Path(params["path"])
        path.mkdir(exist_ok=True, parents=True)
        logger.info(f"Created directory: {path}")
        return {"output": f"Created directory: {path}"}

    def _handle_create_file(self, params: dict) -> ActionResult:
        path = Path(params["path"])
        path.parent.mkdir(exist_ok=True, parents=True)
        # Convert literal "\n" sequences to actual newlines
        content = params["content"].encode().decode("unicode_escape")
        path.write_text(content)
        # Allow filesystem update to complete
        import time
        time.sleep(0.1)
        logger.info(f"Created file: {path}")
        return {"output": f"Created file: {path}"}

    def _handle_create_venv(self, params: dict) -> ActionResult:
        subprocess.run(["python", "-m", "venv", params["path"]], check=True)
        logger.info(f"Created virtual environment: {params['path']}")
        return {"output": f"Created virtual environment: {params['path']}"}

    def _handle_install_deps(self, params: dict) -> ActionResult:
        subprocess.run(["pip", "install"] + params["packages"], check=True)
        logger.info(f"Installed dependencies: {params['packages']}")
        return {"output": f"Installed dependencies: {params['packages']}"}

    def _handle_run_command(self, params: dict) -> ActionResult:
        subprocess.run(params["command"], shell=True, check=True)
        logger.info(f"Ran command: {params['command']}")
        return {"output": f"Ran command: {params['command']}"}

    def _handle_custom_action(self, params: dict) -> ActionResult:
        if self.llm:
            # Use LLM to handle custom actions
            response = self.llm.invoke([{
                "role": "user",
                "content": f"How to implement this custom action: {params['description']}"
            }])
            logger.info(f"Custom action guidance: {response.content}")
            return {"output": f"Custom action guidance: {response.content}"}

    def update_state(self, state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        # Add missing update_state method to update the state
        state.update(updates)
        return state
