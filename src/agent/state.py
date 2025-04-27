from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# class State(TypedDict):
#     """State for the scientific agent graph."""
#     messages: Annotated[List[BaseMessage], add_messages]

from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import AnyMessage, add_messages

class State(TypedDict):
    """State for the scientific agent."""
    messages: Annotated[List[AnyMessage], add_messages]
    plot_paths: List[str]  # For storing paths to generated plots
    
    # Optional additional fields for future use
    dataset_info: Dict[str, Any] = {}  # For caching dataset information
    analysis_results: Dict[str, Any] = {}  # For storing analysis results