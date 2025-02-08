import logging
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class AssistantManager:
    def __init__(self, client: AzureOpenAI):
        self.client = client
        self.assistants = {}
        self.threads = {}
        
    # def create_assistant(self, name: str, instructions: str, tools: list = None):
    #     """Create an assistant with specified configuration."""
    #     try:
    #         if tools is None:
    #             tools = [{"type": "code_interpreter"}]
            
    #         assistant = self.client.beta.assistants.create(
    #             name=name,
    #             instructions=instructions,
    #             tools=tools,
    #             model="o1-preview"
    #         )
    #         self.assistants[name] = assistant
    #         return assistant
    #     except Exception as e:
    #         logger.error(f"Error creating assistant {name}: {str(e)}")
    #         raise

    def get_or_create_thread(self, assistant_name: str):
        """Get existing thread or create a new one for an assistant."""
        if assistant_name not in self.threads:
            self.threads[assistant_name] = self.client.beta.threads.create()
        return self.threads[assistant_name]

    def run_conversation(self, assistant_name: str, prompt: str, instructions: str = None) -> str:
        """Run a conversation with an assistant and return the response."""
        try:
            assistant = self.assistants.get(assistant_name)
            if not assistant:
                raise ValueError(f"Assistant {assistant_name} not found")

            thread = self.get_or_create_thread(assistant_name)
            
            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )

            # Run the thread
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
                instructions=instructions
            )

            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                return messages.data[0].content[0].text.value
            else:
                raise Exception(f"Run failed with status: {run.status}")
                
        except Exception as e:
            logger.error(f"Error in conversation with {assistant_name}: {str(e)}")
            raise
