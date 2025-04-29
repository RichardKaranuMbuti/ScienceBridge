from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.store.memory import InMemoryStore
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks, RunnableConfig
from src.agent.state import State
from src.agent.agent import run_agent, should_continue
from src.agent.tools import (
    fetch_dataset_info, 
    execute_python, 
    explain_graph, 
    install_python_packages, 
    ask_ai,
    db_query_tool,
    print_tool_execution
)

def handle_tool_error(state) -> Dict:
    """Handle errors from tool execution and surface them to the agent."""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    
    # Print tool error for visibility
    print_tool_execution("TOOL-ERROR", "ERROR", f"Error executing tool: {repr(error)}")
    
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\nPlease fix your approach and try again.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: List) -> RunnableWithFallbacks:
    """Create a ToolNode with proper error handling."""
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], 
        exception_key="error"
    )

class ScienceAgent:
    def __init__(self):
        # Create the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the agent graph with proper tool handling."""
        # Initialize the state graph
        graph_builder = StateGraph(State)
        
        # Add agent node
        graph_builder.add_node("agent", run_agent)
        
        # Define tools explicitly to ensure they are properly serializable
        tools = [
            fetch_dataset_info, 
            execute_python, 
            explain_graph,
            install_python_packages,
            ask_ai,
            db_query_tool
        ]
        
        # Add tools node with proper error handling
        tools_node = create_tool_node_with_fallback(tools)
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
        
        # # Add memory persistence
        # memory = MemorySaver() 
        
        # Create a store for tool annotations
        store = InMemoryStore()
        
        # Compile the graph with the store
        return graph_builder.compile(checkpointer=None, store=store) #checkpointer=memory)
    
    def run(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Run the agent with the given user input.
        
        Args:
            user_input: The user's input message
            thread_id: A unique identifier for the conversation thread
        
        Returns:
            The final state of the graph execution
        """
        print("\n" + "="*50)
        print(f"Starting new agent run for thread: {thread_id}")
        print("="*50)
        
        # Configure the thread ID for memory persistence and set recursion limit
        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=50  # Set your desired recursion limit here
        )
        
        # Create the initial state with the user's message
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "plot_paths": []  # Initialize empty plot paths for storing visualization results
        }
        
        # Execute the graph
        result = self.graph.invoke(initial_state, config)
        
        print("\n" + "="*50)
        print("Agent run completed")
        print("="*50 + "\n")
        
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
        print("\n" + "="*50)
        print(f"Continuing conversation for thread: {thread_id}")
        print("="*50)
        
        # Configure the thread ID for memory persistence
        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=50
        )
        
        # Create a state with only the new user message
        new_state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        # Execute the graph, which will automatically load the previous state
        result = self.graph.invoke(new_state, config)
        
        print("\n" + "="*50)
        print("Conversation continuation completed")
        print("="*50 + "\n")
        
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
    
    def stream_run(self, user_input: str, thread_id: str = "default"):
        """
        Stream the agent execution with the given user input.
        
        Args:
            user_input: The user's input message
            thread_id: A unique identifier for the conversation thread
            
        Yields:
            Intermediate states as the agent runs
        """
        print("\n" + "="*50)
        print(f"Starting streaming agent run for thread: {thread_id}")
        print("="*50)
        
        # Configure the thread ID for memory persistence
        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=50
        )
        
        # Create the initial state with the user's message
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "plot_paths": []  # Initialize empty plot paths
        }
        
        # Stream the graph execution
        for chunk in self.graph.stream(initial_state, config, stream_mode="values"):
            yield chunk
        
        print("\n" + "="*50)
        print("Streaming agent run completed")
        print("="*50 + "\n")