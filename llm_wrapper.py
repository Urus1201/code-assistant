import logging
from langchain_openai import ChatOpenAI
from assistant_manager import AssistantManager

logger = logging.getLogger(__name__)

class LLMWrapper:
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.assistant_manager = AssistantManager(client)
        self._setup_assistants()

    def _setup_assistants(self):
        """Initialize different assistants for various tasks."""
        self.assistant_manager.create_assistant(
            "planner",
            "You are an AI assistant that creates detailed development plans for software projects."
        )
        
        self.assistant_manager.create_assistant(
            "reviewer",
            "You are an AI assistant that reviews Python code for best practices, bugs, and improvements.",
            tools=[{"type": "code_interpreter"}, {"type": "retrieval"}]
        )
        
        # Create a new assistant for data visualization
        self.assistant_manager.create_assistant(
            "data_visualization",
            "You are a helpful AI assistant who makes interesting visualizations based on data. "
            "You have access to a sandboxed environment for writing and testing code. "
            "When you are asked to create a visualization you should follow these steps: "
            "1. Write the code. "
            "2. Anytime you write new code display a preview of the code to show your work. "
            "3. Run the code to confirm that it runs. "
            "4. If the code is successful display the visualization. "
            "5. If the code is unsuccessful display the error message and try to revise the code and rerun going through the steps from above again.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4-1106-preview"  # Replace this value with the deployment name for your model.
        )

    def chat(self, prompt: str, system_message: str = None, assistant_name: str = "planner") -> str:
        """Enhanced chat method using assistants API."""
        try:
            instructions = system_message if system_message else None
            return self.assistant_manager.run_conversation(
                assistant_name,
                prompt,
                instructions
            )
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise
