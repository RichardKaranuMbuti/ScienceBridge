from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from src.agent.state import State
from src.agent.agent import run_agent, should_continue
from src.agent.tools import ask_ai, execute_python, human_assistance

class AgentGraph:
    def __init__(self):
        # Create the graph
        self.graph = self._build_graph()
    
    def _build_graph(self):
        # Initialize the state graph
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("agent", run_agent)
        
        # Add tools node - simplified version without debugging
        tools_node = ToolNode(tools=[ask_ai, execute_python, human_assistance])
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
    
    def handle_human_interrupt(self, human_response: Dict[str, Any], thread_id: str = "default"):
        """
        Handle a human response to an interrupt.
        
        Args:
            human_response: The human's response to the interrupt
            thread_id: The identifier for the conversation thread
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # The Command object is created automatically by LangGraph when we resume
        self.graph.invoke(human_response, config)
    
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
    
    def get_state_history(self, thread_id: str = "default"):
        """
        Get the full history of states for time travel functionality.
        
        Args:
            thread_id: The identifier for the conversation thread
        
        Returns:
            The history of states for the conversation
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        return self.graph.get_state_history(config)
    
    def resume_from_checkpoint(self, checkpoint_id: str, thread_id: str = "default"):
        """
        Resume execution from a specific checkpoint for time travel.
        
        Args:
            checkpoint_id: The specific checkpoint ID to resume from
            thread_id: The identifier for the conversation thread
        
        Returns:
            The result of continuing execution from the checkpoint
        """
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }
        
        # Resume execution from the specified checkpoint
        result = self.graph.invoke(None, config)
        
        return result


# Example usage
if __name__ == "__main__":
    # Create the agent graph
    agent_graph = AgentGraph()
    
    # Start a conversation
    result = agent_graph.run("Which descriptors correlate most with bioactivity?", "test-thread")
    
    # Print the conversation
    print("---- CONVERSATION RESULT ----")
    for message in result["messages"]:
        print(f"{message.type}: {message.content}")
        
        # Print tool calls if any
        if hasattr(message, "tool_calls") and message.tool_calls:
            print("TOOL CALLS:")
            for tool_call in message.tool_calls:
                print(f"  - {tool_call['name']}: {tool_call['args']}")
                
        # Print additional metadata if available
        if hasattr(message, "additional_kwargs") and message.additional_kwargs:
            print(f"ADDITIONAL DATA: {message.additional_kwargs}")
    
    print("---------------------------")