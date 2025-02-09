import logging
from typing import Annotated, Dict, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI
import yaml
from agents import PlannerAgent, ExecutorAgent, ReviewerAgent, RunnerAgent, MonitorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import getpass
import os

os.environ["AZURE_OPENAI_API_KEY"] = getpass.getpass("Azure OpenAI API key")
os.environ["AZURE_OPENAI_ENDPOINT"] = getpass.getpass("Azure OpenAI endpoint")

# AZURE_OPENAI_DEPLOYMENT_NAME = getpass.getpass("Azure OpenAI deployment name")

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    plan: List[str]
    current_step: int
    status: str
    errors: List[str]
    next: str

def should_continue(state: AgentState) -> bool:
    """Determine if we should continue the workflow."""
    return state["status"] not in ["completed", "failed"]

def monitoring_condition(state: AgentState) -> str:
    """
    Determines next step based on monitoring results:
    - If status is 'completed' -> END
    - If there are errors -> back to planner
    """
    if state.get("status") == "completed" and not state.get("errors"):
        return END
    return "planner"

def create_agent_graph(llm: AzureChatOpenAI):
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import tools_condition

    # Define agent nodes
    planner = PlannerAgent(llm)
    executor = ExecutorAgent(llm)
    reviewer = ReviewerAgent(llm)
    runner = RunnerAgent()
    monitor = MonitorAgent(llm)

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add agent nodes
    workflow.add_node("planner", planner.run)
    workflow.add_node("executor", executor.execute_plan)
    workflow.add_node("reviewer", reviewer.review_and_refine)
    workflow.add_node("runner", runner.run_main)
    workflow.add_node("monitoring", monitor.run)

    # Define graph edges with conditional routing
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "reviewer")
    workflow.add_edge("reviewer", "runner")
    workflow.add_edge("runner", "monitoring")
    
    # Add conditional edge from monitoring
    workflow.add_conditional_edges(
        "monitoring",
        monitoring_condition,
        {
            END: END,
            "planner": "planner"
        }
    )

    return workflow.compile()

def stream_graph_updates(graph, user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

def main():

    llm = AzureChatOpenAI(
        deployment_name="o1-preview", openai_api_version="2024-08-01-preview"
    )

    # Create the workflow graph
    workflow = create_agent_graph(llm)

    # Main loop to take human input from the console
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(workflow, user_input)
        except Exception as e:
           return e

if __name__ == "__main__":
    main()
