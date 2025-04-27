from src.agent.graph import ScienceAgent
from src.python_executor.simple_python_executor import SimplePythonExecutor
import os
import uuid
import time
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Initialize Rich console for better terminal output
console = Console()

def print_message_history(messages):
    """Print the message history in a readable format using Rich."""
    for i, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            console.print(Panel(
                message.content,
                title=f"[bold blue]Human Message {i+1}[/bold blue]",
                border_style="blue"
            ))
        
        elif isinstance(message, AIMessage):
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Print AI message with tool calls
                tool_calls_text = ""
                for tc in message.tool_calls:
                    tool_calls_text += f"\n[bold cyan]Tool:[/bold cyan] {tc['name']}\n"
                    if 'args' in tc:
                        if isinstance(tc['args'], dict):
                            for k, v in tc['args'].items():
                                v_display = f"{v[:100]}..." if isinstance(v, str) and len(v) > 100 else v
                                tool_calls_text += f"[bold cyan]Arg:[/bold cyan] {k} = {v_display}\n"
                        else:
                            tool_calls_text += f"[bold cyan]Args:[/bold cyan] {tc['args']}\n"
                
                if message.content:
                    content = f"{message.content}\n\n[bold]Tool Calls:[/bold]{tool_calls_text}"
                else:
                    content = f"[bold]Tool Calls:[/bold]{tool_calls_text}"
                
                console.print(Panel(
                    Markdown(content),
                    title=f"[bold green]AI Message {i+1}[/bold green]",
                    border_style="green"
                ))
            else:
                # Print regular AI message
                console.print(Panel(
                    Markdown(message.content),
                    title=f"[bold green]AI Message {i+1}[/bold green]",
                    border_style="green"
                ))
        
        elif isinstance(message, ToolMessage):
            # Try to detect code in the tool output
            if "```" in message.content:
                # This could contain code blocks
                console.print(Panel(
                    Markdown(message.content),
                    title=f"[bold yellow]Tool Output {i+1} ({message.name})[/bold yellow]",
                    border_style="yellow"
                ))
            else:
                console.print(Panel(
                    message.content,
                    title=f"[bold yellow]Tool Output {i+1} ({message.name})[/bold yellow]",
                    border_style="yellow"
                ))
        else:
            # Generic message handling
            console.print(Panel(
                str(message.content),
                title=f"[bold]Message {i+1} ({message.type})[/bold]",
                border_style="white"
            ))

def initialize_environment():
    """Initialize the Python executor environment."""
    console.print(Panel(
        "Setting up Python execution environment for data analysis and visualization...",
        title="[bold]Initialization[/bold]",
        border_style="blue"
    ))
    
    # Initialize Python executor with default packages
    executor = SimplePythonExecutor(
        venv_path=os.path.join(os.getcwd(), "venvs"),
        auto_install=True
    )
    
    console.print(Panel(
        "✅ Python execution environment initialized successfully!",
        title="[bold]Initialization Complete[/bold]",
        border_style="green"
    ))
    return executor

def main():
    """Run the science agent."""
    console.print(Panel(
        "[bold]This agent can analyze scientific datasets, create visualizations, and provide insights.[/bold]\n\n"
        "Built with [blue]LangGraph[/blue] and powered by advanced language models, this agent can:\n"
        "- Analyze datasets and extract patterns\n"
        "- Create visualizations based on your requirements\n"
        "- Provide detailed scientific insights\n"
        "- Install and use Python packages as needed\n\n"
        "Type 'exit' to quit.",
        title="[bold blue]🧪 Scientific Data Analysis Agent[/bold blue]",
        border_style="blue"
    ))
    
    # Initialize the Python execution environment first
    executor = initialize_environment()
    
    # Create the agent
    agent = ScienceAgent()
    thread_id = f"science-session-{uuid.uuid4()}"
    
    try:
        while True:
            user_input = console.input("\n[bold blue]Enter your research question:[/bold blue] ")
            if user_input.lower() == 'exit':
                break
                
            console.print("\n[bold yellow]Processing your question...[/bold yellow]\n")
            
            # Option 1: Run with standard invoke
            result = agent.run(user_input, thread_id)
            
            # Option 2: Run with streaming for more responsive feedback
            # latest_messages = []
            # for chunk in agent.stream_run(user_input, thread_id):
            #     latest_messages = chunk.get("messages", [])
            #     # You could print intermediate results here if desired
            # result = {"messages": latest_messages}
            
            # Print the conversation history
            print_message_history(result["messages"])
            
            # Add a small pause between conversations
            time.sleep(1)
    
    except KeyboardInterrupt:
        console.print("\n[bold]Exiting...[/bold]")
    finally:
        # Clean up resources
        executor.cleanup()
        console.print(Panel(
            "Thank you for using the Scientific Data Analysis Agent!",
            title="[bold]Session Ended[/bold]",
            border_style="blue"
        ))

if __name__ == "__main__":
    main()