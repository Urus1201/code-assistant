import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ReviewerAgent:
    def __init__(self, llm):
        self.llm = llm

    def review_and_refine(self, state: dict) -> dict:
        plan = state.get("plan", {})
        context = plan.get("context", {})
        project_path = context.get("last_created_dir", "project")
        logger.info(f"Reviewing code in {project_path}")
        
        try:
            # Try main.py; if not present, fall back to last_created_file from context
            main_path = Path(project_path) / "main.py"
            if not main_path.exists():
                alt = context.get("last_created_file", "")
                main_path = Path(project_path) / alt if alt else main_path
            test_path = Path(project_path) / "test_sum_even_numbers.py"
            
            main_code = self._read_file(main_path)
            test_code = self._read_file(test_path)
            
            if self.llm:
                # Use invoke instead of chat
                review = self.llm.invoke([{
                    "role": "user",
                    "content": f"Review this Python code:\n\n{main_code}\n\nTests:\n{test_code}"
                }]).content
                logger.info(f"Code review results:\n{review}")
                self._implement_suggestions(review, project_path)
                state.setdefault("messages", []).append(
                    {"role": "system", "content": f"Reviewer comments: {review}"}
                )
            return state

        except Exception as e:
            logger.error(f"Error during code review: {e}")
            state.setdefault("errors", []).append(str(e))
            return state

    def _implement_suggestions(self, review: str, project_path: str):
        """Implement suggestions from the code review."""
        if self.llm:
            prompt = f"""
            Based on this review:
            {review}
            
            Generate the improved version of the code that implements these suggestions.
            Return only the improved code without explanations.
            """
            try:
                # Remove unsupported assistant_name parameter
                improved_code = self.llm.invoke(prompt)
                if improved_code:
                    self._write_improved_code(improved_code, project_path)
            except Exception as e:
                logger.error(f"Error implementing suggestions: {e}")

    def _read_file(self, path: Path) -> str:
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            return ""
