from src.agent.graph import ScienceAgent
from src.python_executor.simple_python_executor import SimplePythonExecutor
import os

def print_message_history(messages):
    """Print the message history in a readable format."""
    for i, message in enumerate(messages):
        print(f"\n--- Message {i+1} ({message.type}) ---")
        print(message.content)
        
        # Print tool calls if any
        if hasattr(message, "tool_calls") and message.tool_calls:
            print("\nTool Calls:")
            for tool_call in message.tool_calls:
                print(f"  - Tool: {tool_call['name']}")
                if 'args' in tool_call:
                    if isinstance(tool_call['args'], dict):
                        for k, v in tool_call['args'].items():
                            print(f"    - {k}: {v[:100]}..." if isinstance(v, str) and len(v) > 100 else f"    - {k}: {v}")
                    else:
                        print(f"    - args: {tool_call['args']}")

def initialize_environment():
    """Initialize the Python executor environment."""
    print("Initializing Python execution environment...")
    
    # Create plots directory
    plots_dir = os.path.join(os.getcwd(), "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # Initialize Python executor with default packages
    executor = SimplePythonExecutor(
        venv_path=os.path.join(os.getcwd(), "venvs"),
        plots_dir=plots_dir,
        auto_install=True
    )
    
    print("Python execution environment initialized.")
    return executor

def main():
    """Run the science agent."""
    print("=== Scientific Data Analysis Agent ===")
    print("This agent can analyze scientific datasets, create visualizations, and provide insights.")
    
    # Initialize the Python execution environment first
    executor = initialize_environment()
    
    print("Type 'exit' to quit.\n")
    
    # Create the agent
    agent = ScienceAgent()
    thread_id = "science-session-1"
    
    while True:
        user_input = input("\nEnter your research question: ")
        if user_input.lower() == 'exit':
            break
            
        print("\nProcessing your question...\n")
        
        # Run the agent
        result = agent.run(user_input, thread_id)
        
        # Print the conversation history
        print_message_history(result["messages"])
    
    # Clean up resources
    executor.cleanup()

if __name__ == "__main__":
    main()

# def main():
#     """Run the science agent with a predefined research question."""
#     print("=== Scientific Data Analysis Agent ===")
#     print("This agent can analyze scientific datasets, create visualizations, and provide insights.")
    
#     # Create the agent
#     agent = ScienceAgent()
#     thread_id = "science-session-1"
    
#     # Define the research question as a variable
#     research_question = "Which descriptors correlate most with bioactivity?"
    
#     print(f"\nResearch Question: {research_question}")
#     print("\nProcessing your question...\n")
    
#     # Run the agent with the predefined question
#     result = agent.run(research_question, thread_id)
    
#     # Print the conversation history
#     print_message_history(result["messages"])

# if __name__ == "__main__":
#     main()