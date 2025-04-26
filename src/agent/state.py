from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    """State for the scientific agent graph."""
    messages: Annotated[List[BaseMessage], add_messages]