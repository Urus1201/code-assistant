from typing import Dict, Any
from .base_agent import BaseAgent
from .types import Plan, Action, ActionType, StepValidation
from langchain_core.messages import AIMessage
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            messages = state["messages"]
            objective = messages[-1].content
            context = state.get("context", {})
            
            if self.llm:
                plan = self.create_plan(objective, context)
                state = self.add_message(
                    state,
                    AIMessage(content=self._format_plan_summary(plan))
                )
                return self.update_state(state, {
                    "plan": plan,
                    "status": "planning_completed",
                    "next": "executor",
                    "context": plan["context"]
                })
            
        except Exception as e:
            self.log_error(e, "plan creation")
            return self.update_state(state, {
                "status": "error",
                "errors": state.get("errors", []) + [str(e)],
                "next": "monitoring"
            })

    def create_plan(self, objective: str, context: Dict[str, Any]) -> Plan:
        logger.info(f"Creating plan for objective: {objective}")
        
        prompt = self._create_planning_prompt(objective, context)
        
        if self.llm:
            try:
                response = self.llm.invoke([{"role": "user", "content": prompt}])
                plan_dict = self._parse_llm_response(response.content)
                
                # Add unique IDs and proper validation to each action
                plan_dict["actions"] = [
                    self._enhance_action(action) 
                    for action in plan_dict["actions"]
                ]
                # Add context if not present
                plan_dict["context"] = {**context, **plan_dict.get("context", {})}
                plan_dict["status"] = "planning"
                return Plan(**plan_dict)
            except Exception as e:
                logger.error(f"Failed to create plan, falling back to default: {e}")
                return e #self._create_default_plan(objective, context)

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate LLM response, cleaning it if necessary."""
        try:
            # Try to find JSON content within the response
            content = content.strip()
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)
            raise ValueError("No JSON object found in response")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Problematic content: {content}")
            raise

    def _create_default_plan(self, objective: str, context: Dict[str, Any]) -> Plan:
        """Create a minimal valid plan when the LLM response fails."""
        return Plan(
            objective=objective,
            actions=[
                Action(
                    id=str(uuid.uuid4()),
                    type=ActionType.CUSTOM,
                    params={"description": "Analyze the objective"},
                    description="Analyze the objective and create detailed plan",
                    validation={"type": "custom", "criteria": "completed"},
                    dependencies=[],
                    result=None
                )
            ],
            context=context,
            dependencies=[],
            estimated_time="5 minutes",
            requirements=[],
            status="planning",
            current_step=None
        )

    def _enhance_action(self, action: Dict[str, Any]) -> Action:
        """Add ID and proper validation to an action"""
        action["id"] = str(uuid.uuid4())
        if "validation" not in action:
            action["validation"] = self._create_default_validation(action)
        action["result"] = None
        return Action(**action)

    def _create_default_validation(self, action: Dict[str, Any]) -> StepValidation:
        """Create default validation based on action type"""
        if action["type"] == ActionType.CREATE_DIR:
            return {
                "type": "file_exists",
                "criteria": action["params"]["path"],
                "expected_result": True
            }
        elif action["type"] == ActionType.CREATE_FILE:
            return {
                "type": "file_exists",
                "criteria": action["params"]["path"],
                "expected_result": True
            }
        # Add more default validations...
        return {
            "type": "custom",
            "criteria": "action_completed",
            "expected_result": True
        }

    def _create_planning_prompt(self, objective: str, context: Dict[str, Any]) -> str:
        return f"""You are a software development planner. Create a detailed plan for this objective: {objective}

IMPORTANT: Respond ONLY with a JSON object. Do not include any other text.

Required JSON structure:
{{
    "objective": "{objective}",
    "actions": [
        {{
            "type": "action_type",
            "params": {{"key": "value"}},
            "description": "human readable description",
            "dependencies": []
        }}
    ],
    "context": {json.dumps(context)},
    "dependencies": [],
    "estimated_time": "estimated time",
    "requirements": []
}}

Available action types: {[e.value for e in ActionType]}

Remember:
1. Return ONLY the JSON object
2. Make sure all JSON is properly formatted
3. Include at least one action
4. All actions must have a valid type from the list provided"""

    def _format_plan_summary(self, plan: Plan) -> str:
        summary = [f"Objective: {plan['objective']}\n"]
        for i, action in enumerate(plan['actions'], 1):
            summary.append(f"{i}. {action['description']}")
        return "\n".join(summary)

