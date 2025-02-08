import os
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ExecutorAgent:
    def __init__(self, llm):
        self.llm = llm

    def execute_plan(self, plan: list):
        for step in plan:
            try:
                logger.info(f"Executing step: {step}")
                if "Create directory" in step:
                    self._create_directory("factorial_app")
                elif "Initialize Python virtual environment" in step:
                    self._create_venv("factorial_app/.venv")
                elif "Generate requirements.txt" in step:
                    requirements = ["click"]
                    self._write_requirements("factorial_app/requirements.txt", requirements)
                elif "Generate main.py" in step:
                    code = self._generate_main_py()
                    self._write_file("factorial_app/main.py", code)
                elif "Generate test_factorial.py" in step:
                    test_code = self._generate_test_py()
                    self._write_file("factorial_app/test_factorial.py", test_code)
                elif "Install dependencies" in step:
                    self._install_requirements("factorial_app/.venv", "factorial_app/requirements.txt")
                else:
                    logger.warning(f"Unknown step: {step}")
            except Exception as e:
                logger.error(f"Error executing step {step}: {str(e)}")
                raise

    def _create_directory(self, path_str: str):
        path = Path(path_str)
        path.mkdir(exist_ok=True, parents=True)
        logger.info(f"Created directory: {path_str}")

    def _create_venv(self, venv_path_str: str):
        venv_path = Path(venv_path_str)
        try:
            if not venv_path.exists():
                subprocess.run(["python", "-m", "venv", venv_path_str], check=True)
            logger.info(f"Created virtual env: {venv_path_str}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            raise

    def _write_requirements(self, file_path: str, requirements: list):
        with open(file_path, "w") as f:
            for req in requirements:
                f.write(req + "\n")
        logger.info(f"Wrote requirements.txt: {requirements}")

    def _generate_main_py(self) -> str:
        return """\
import click

def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n-1)

@click.command()
@click.argument('number', type=int)
def main(number):
    \"""
    Calculate factorial of a given integer.
    \"""
    result = factorial(number)
    click.echo(f"Factorial of {number} is {result}")

if __name__ == '__main__':
    main()
"""

    def _generate_test_py(self) -> str:
        return """\
import unittest
from main import factorial

class TestFactorial(unittest.TestCase):
    def test_factorial_0(self):
        self.assertEqual(factorial(0), 1)

    def test_factorial_1(self):
        self.assertEqual(factorial(1), 1)

    def test_factorial_5(self):
        self.assertEqual(factorial(5), 120)

if __name__ == '__main__':
    unittest.main()
"""

    def _write_file(self, file_path: str, code: str):
        with open(file_path, "w") as f:
            f.write(code)
        logger.info(f"Wrote file: {file_path}")

    def _install_requirements(self, venv_path_str: str, req_file_str: str):
        try:
            if os.name == "nt":
                pip_executable = Path(venv_path_str) / "Scripts" / "pip.exe"
            else:
                pip_executable = Path(venv_path_str) / "bin" / "pip"
            subprocess.run([str(pip_executable), "install", "-r", req_file_str], check=True)
            logger.info("Installed dependencies")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise

    def install_module(self, module_name: str):
        try:
            subprocess.run(["pip", "install", module_name], check=True)
            logger.info(f"Installed module: {module_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install module {module_name}: {e}")
            raise

    def check_file_path(self, file_path: str):
        if not Path(file_path).exists():
            logger.error(f"File path does not exist: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        logger.info(f"File path is valid: {file_path}")

    def fix_code(self, error_type: str):
        # In a real scenario, this would use an LLM to modify the code.
        if error_type == "undefined_variable":
            logger.warning("Attempting to fix undefined variable error (dummy fix)")
            # Dummy fix: Add a variable definition to main.py
            main_py_path = Path("factorial_app") / "main.py"
            with open(main_py_path, "a") as f:
                f.write("\n# Dummy fix: Define missing variable\nmissing_variable = 0\n")
        else:
            logger.warning("Attempting to fix general code error (dummy fix)")
            # Dummy fix: Add a comment to main.py
            main_py_path = Path("factorial_app") / "main.py"
            with open(main_py_path, "a") as f:
                f.write("\n# Dummy fix: General code fix\n")
