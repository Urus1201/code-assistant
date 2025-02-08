import subprocess
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class RunnerAgent:
    def run_main(self, project_path: str, venv_path_str: str, args=None):
        if not args:
            args = ["5"]
        try:
            python_exec = Path(venv_path_str) / ("Scripts" if os.name == "nt" else "bin") / "python"
            if not python_exec.exists():
                error_message = f"Python executable not found: {python_exec}"
                logger.error(error_message)
                raise FileNotFoundError(error_message)
            main_path = Path(project_path) / "main.py"
            logger.info(f"Running: {python_exec} {main_path} {args}")
            
            result = subprocess.run(
                [str(python_exec), str(main_path)] + args, 
                capture_output=True, 
                text=True,
                check=True
            )
            logger.info(f"Output: {result.stdout}")
            return result
        except FileNotFoundError as e:
            logger.error(f"Python executable not found: {e}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running main.py: {e.stderr}")
            raise
