"""
LangGraph Workflow with LangSmith Observability.
Provides full traceability of the multi-agent pharmacy system.

Agent Flow:
1. pharmacist -> Parses user request into structured order
2. safety -> Validates stock and prescription requirements
3. confirmation -> Asks user for confirmation before placing order (NEW - human-friendly)
4. execution -> Places order and sends notifications

Each step is traced for observability.
"""
from langgraph.graph import StateGraph, END
from agents.state_schema import AgentState
from agents.pharmacist_agent import pharmacist_agent
from agents.safety_agent import safety_agent
from agents.confirmation_agent import confirmation_agent
from agents.execution_agent import execution_agent
import os

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "swasthya-sarthi")

# Configure LangSmith if available
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    print(f"[Graph] LangSmith enabled - Project: {LANGSMITH_PROJECT}")
else:
    print("[Graph] LangSmith not configured - set LANGSMITH_API_KEY for tracing")

# Create the workflow
workflow = StateGraph(AgentState)

# Add nodes (agents)
workflow.add_node("pharmacist", pharmacist_agent)
workflow.add_node("safety", safety_agent)
workflow.add_node("confirmation", confirmation_agent)
workflow.add_node("execution", execution_agent)

# Set entry point
workflow.set_entry_point("pharmacist")

# Main conversation flow: pharmacist -> safety -> confirmation -> execution
# The confirmation agent will ask user before order is placed
workflow.add_edge("pharmacist", "safety")
workflow.add_edge("safety", "confirmation")
workflow.add_edge("confirmation", "execution")
workflow.add_edge("execution", END)

# Compile the workflow
app_graph = workflow.compile()

# Export for use in other modules
__all__ = ["app_graph"]
