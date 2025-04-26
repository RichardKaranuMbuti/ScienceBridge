# state.py
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    """State for the agent graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    # Additional state fields can be added here if needed
    # For example:
    # current_task: str
    # execution_results: List[dict]