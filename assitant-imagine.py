import os
import subprocess
from pathlib import Path

###############################################
# 1) PLANNER AGENT
###############################################
class PlannerAgent:
    def __init__(self, llm):
        self.llm = llm  # Some language model interface

    def create_plan(self, user_objective: str) -> list:
        """
        Given the user's objective, generate a step-by-step plan.
        The plan is a list of steps (strings or structured objects).
        """
        # Example prompt to LLM (pseudocode)
        # response = self.llm.chat(f"Create a step-by-step plan to accomplish: {user_objective}")
        # plan = parse(response)
        # For demonstration, return a static plan:
        plan = [
            "Create directory factorial_app",
            "Initialize Python virtual environment .venv",
            "Generate requirements.txt with 'click' library",
            "Generate main.py with factorial code and CLI logic",
            "Generate test_factorial.py with unit tests",
            "Install dependencies",
        ]
        return plan


###############################################
# 2) EXECUTOR AGENT
###############################################
class ExecutorAgent:
    def __init__(self, llm):
        self.llm = llm

    def execute_plan(self, plan: list):
        for step in plan:
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
                print(f"Unknown step: {step}")

    def _create_directory(self, path_str: str):
        path = Path(path_str)
        path.mkdir(exist_ok=True, parents=True)
        print(f"[Executor] Created directory: {path_str}")

    def _create_venv(self, venv_path_str: str):
        venv_path = Path(venv_path_str)
        if not venv_path.exists():
            subprocess.run(["python", "-m", "venv", venv_path_str], check=True)
        print(f"[Executor] Created virtual env: {venv_path_str}")

    def _write_requirements(self, file_path: str, requirements: list):
        with open(file_path, "w") as f:
            for req in requirements:
                f.write(req + "\n")
        print(f"[Executor] Wrote requirements.txt: {requirements}")

    def _generate_main_py(self) -> str:
        # This would normally come from an LLM.
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
        # This would normally come from an LLM or from a template.
        return """\
import unittest
from factorial_app.main import factorial

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
        print(f"[Executor] Wrote file: {file_path}")

    def _install_requirements(self, venv_path_str: str, req_file_str: str):
        if os.name == "nt":
            pip_executable = Path(venv_path_str) / "Scripts" / "pip.exe"
        else:
            pip_executable = Path(venv_path_str) / "bin" / "pip"
        subprocess.run([str(pip_executable), "install", "-r", req_file_str], check=True)
        print("[Executor] Installed dependencies")


###############################################
# 3) REVIEWER AGENT
###############################################
class ReviewerAgent:
    def __init__(self, llm):
        self.llm = llm

    def review_and_refine(self, project_path: str):
        """
        Loads code, sends it to an LLM for review, and if improvements are found,
        rewrites the files. For simplicity, we'll just print a message here.
        """
        # Real approach: read the files, pass them to LLM with "Please review the code"
        # Possibly parse suggestions, rewrite files as needed.
        # For demonstration, we pretend no changes needed.
        print("[Reviewer] Code reviewed. No critical issues found, but potential improvements might be suggested.")


###############################################
# 4) RUNNER AGENT
###############################################
class RunnerAgent:
    def run_main(self, project_path: str, venv_path_str: str, args=None):
        """
        Activates the venv and runs main.py. For simplicity, we won't actually
        activate in-process but call python with the venv's path.
        """
        if not args:
            args = ["5"]  # default argument for demonstration
        python_exec = Path(venv_path_str) / ("Scripts" if os.name == "nt" else "bin") / "python"
        main_path = Path(project_path) / "main.py"
        print(f"[Runner] Running: {python_exec} {main_path} {args}")
        result = subprocess.run([str(python_exec), str(main_path)] + args, capture_output=True, text=True)
        print("[Runner] Output:")
        print(result.stdout)
        if result.stderr:
            print("[Runner] Errors:", result.stderr)


###############################################
# ORCHESTRATION / MAIN DRIVER
###############################################
def main():
    # In a real scenario, you'd have a real LLM object; we use `None` placeholders.
    llm = None

    # Step 0: User input
    user_objective = "Create a CLI that calculates factorial for a user-input integer."

    # Step 1: Planner Agent -> creates plan
    planner = PlannerAgent(llm)
    plan = planner.create_plan(user_objective)
    print("[System] Plan created:", plan)

    # Step 2: Executor Agent -> sets up environment & code
    executor = ExecutorAgent(llm)
    executor.execute_plan(plan)

    # Step 3: Reviewer Agent -> checks code and refines if needed
    reviewer = ReviewerAgent(llm)
    reviewer.review_and_refine("factorial_app")

    # Step 4: Runner Agent -> runs main.py
    runner = RunnerAgent()
    runner.run_main("factorial_app", "factorial_app/.venv")

if __name__ == "__main__":
    main()