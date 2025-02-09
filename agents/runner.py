import subprocess
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class RunnerAgent:
    def run_main(self, state: dict) -> dict:
        # Extract project path from state
        plan = state.get("plan", {})
        context = plan.get("context", {})
        project_path = context.get("last_created_dir", ".")
        
        # Determine the main file to run (defaulting to "main.py")
        main_file = context.get("main_file", "main.py")
        main_path = Path(project_path) / main_file
        
        # If not found, try to fall back to the last created file
        if not main_path.exists():
            fallback = context.get("last_created_file", "")
            if fallback:
                main_file = fallback
                main_path = Path(project_path) / main_file
        if not main_path.exists():
            error_message = f"{main_file} not found in project path: {project_path}"
            logger.error(error_message)
            state.setdefault("errors", []).append(error_message)
            state.update({"status": "error"})
            return state

        # Use venv path if provided; fallback to system python
        venv_path = context.get("venv_path", None)
        if venv_path:
            python_exec = Path(venv_path) / ("Scripts" if os.name == "nt" else "bin") / "python"
            if not python_exec.exists():
                logger.error(f"Python executable not found in venv: {python_exec}")
                raise FileNotFoundError(f"Python executable not found: {python_exec}")
        else:
            python_exec = "python"

        try:
            logger.info(f"Running: {python_exec} {main_path}")
            result = subprocess.run(
                [str(python_exec), str(main_path)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Output: {result.stdout}")
            state.setdefault("messages", []).append(
                {"role": "system", "content": f"Runner output: {result.stdout}"}
            )
            state.update({"last_run_output": result.stdout})
            return state
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {main_file}: {e.stderr}")
            state.setdefault("errors", []).append(e.stderr)
            state.update({"status": "error"})
            return state
