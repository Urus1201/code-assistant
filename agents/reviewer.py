import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ReviewerAgent:
    def __init__(self, llm):
        self.llm = llm

    def review_and_refine(self, project_path: str):
        logger.info(f"Reviewing code in {project_path}")
        
        try:
            main_code = self._read_file(Path(project_path) / "main.py")
            test_code = self._read_file(Path(project_path) / "test_factorial.py")

            if self.llm:
                review = self.llm.chat(
                    f"Review this Python code:\n\n{main_code}\n\nTests:\n{test_code}",
                    system_message="Analyze the code for bugs, improvements, and best practices.",
                    assistant_name="reviewer"
                )
                logger.info(f"Code review results:\n{review}")
                
                # Implement suggestions from review
                self._implement_suggestions(review, project_path)
            
            return True

        except Exception as e:
            logger.error(f"Error during code review: {e}")
            return False

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
                improved_code = self.llm.chat(
                    prompt,
                    assistant_name="reviewer"
                )
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
