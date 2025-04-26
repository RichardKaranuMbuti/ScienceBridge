from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from src.agent.state import State
from src.agent.agent import run_agent, should_continue
from src.agent.tools import fetch_dataset_info, execute_python, db_query_tool, install_python_packages, ask_ai

class ScienceAgent:
    def __init__(self):
        # Create the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the agent graph."""
        # Initialize the state graph
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("agent", run_agent)
        
        # Add tools node with all available tools
        tools_node = ToolNode(tools=[
            fetch_dataset_info, 
            execute_python, 
            db_query_tool, 
            install_python_packages,
            ask_ai
        ])
        graph_builder.add_node("tools", tools_node)
        
        # Add edges
        graph_builder.add_edge(START, "agent")
        graph_builder.add_conditional_edges(
            "agent", 
            should_continue, 
            {
                "tools": "tools",
                "end": END
            }
        )
        graph_builder.add_edge("tools", "agent")
        
        # Add memory persistence
        memory = MemorySaver()
        
        # Compile the graph
        return graph_builder.compile(checkpointer=memory)
    
    def run(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Run the agent with the given user input.
        
        Args:
            user_input: The user's input message
            thread_id: A unique identifier for the conversation thread
        
        Returns:
            The final state of the graph execution
        """
        # Configure the thread ID for memory persistence
        config = {"configurable": {"thread_id": thread_id}}
        
        # Create the initial state with the user's message
        initial_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        # Execute the graph
        result = self.graph.invoke(initial_state, config)
        
        return result
    
    def continue_conversation(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Continue an existing conversation with new user input.
        
        Args:
            user_input: The user's new input message
            thread_id: The identifier for the existing conversation thread
        
        Returns:
            The final state of the graph execution
        """
        # Configure the thread ID for memory persistence
        config = {"configurable": {"thread_id": thread_id}}
        
        # Create a state with only the new user message
        new_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        # Execute the graph, which will automatically load the previous state
        result = self.graph.invoke(new_state, config)
        
        return result
    
    def get_conversation_history(self, thread_id: str = "default"):
        """
        Get the full history of the conversation.
        
        Args:
            thread_id: The identifier for the conversation thread
        
        Returns:
            A list of the full conversation history
        """
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.get_state(config)
        
        return state.values.get("messages", [])