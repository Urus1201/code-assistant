from typing import Dict, Any, List
from .base_agent import BaseAgent
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            messages = state["messages"]
            objective = messages[-1].content
            
            if self.llm:
                plan = self.create_plan(objective)
                state = self.add_message(
                    state,
                    AIMessage(content=f"Created plan with {len(plan)} steps")
                )
                return self.update_state(state, {
                    "plan": plan,
                    "current_step": 0,
                    "status": "planning_completed",
                    "next": "executor"
                })
            
        except Exception as e:
            self.log_error(e, "plan creation")
            return self.update_state(state, {
                "status": "error",
                "errors": state.get("errors", []) + [str(e)],
                "next": "monitoring"
            })

    def create_plan(self, user_objective: str) -> List[str]:
        logger.info(f"Creating plan for objective: {user_objective}")
        if self.llm:
            # Combine system instructions with the user prompt since 'system' role is unsupported.
            content = (
                "You are a software project planner. Return only the numbered list of steps.\n\n"
                f"Create a detailed development plan for: {user_objective}\n\n"
                "The plan should be organized as a numbered list and include:\n"
                "1. Environment setup (directory structure, virtual environment)\n"
                "2. Dependencies and requirements\n"
                "3. Core implementation files needed\n"
                "4. Test files and test cases\n"
                "5. Additional tooling (linting, formatting)\n\n"
                "Each step should be clear and actionable."
            )
            messages = [{"role": "user", "content": content}]
            try:
                response = self.llm.invoke(messages)
                logger.info(f"Generated plan using LLM: {response}")
                return self._parse_plan(response.content)
            except Exception as e:
                logger.error(f"Error generating plan with LLM: {e}")
                raise e

    def _parse_plan(self, llm_response: str) -> List[str]:
        # Simple parsing logic - split by newlines and clean up
        steps = [step.strip() for step in llm_response.split('\n') 
                if step.strip() and not step.startswith('#')]
        return steps

