from typing import Annotated
from langchain_core.tools import tool, ToolException
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt
import json

# Import your existing implementations
from src.openai_tool.client import OpenAIClient
from src.python_executor.simple_python_executor import SimplePythonExecutor

# Initialize the Python executor once
python_executor = SimplePythonExecutor()

@tool
def ask_ai(question: str) -> str:
    """
    Query specialized knowledge sources about scientific concepts.
    
    Args:
        question: The scientific question to research
        
    Returns:
        Detailed information about the scientific concept
    """
    try:
        # Use your existing OpenAIClient implementation
        answer = OpenAIClient.query(question)
        return answer
    except Exception as e:
        raise ToolException(f"Error querying AI: {str(e)}")

@tool
def execute_python(code: str) -> str:
    """
    Execute Python code for data analysis and visualization.
    
    Args:
        code: Python code to execute (can include data analysis, visualization, etc.)
        
    Returns:
        The output of the code execution, including any text output and references to generated visualizations
    """
    try:
        # Execute the code using your SimplePythonExecutor
        result = python_executor.execute_code(code)
        
        # Format the response in a readable way
        response_parts = []
        
        # Add stdout if available
        if result.get("stdout"):
            response_parts.append(f"Output:\n{result['stdout']}")
        
        # Add error information if execution failed
        if not result["success"]:
            error_msg = result.get("stderr", "Unknown error")
            response_parts.append(f"Error:\n{error_msg}")
        
        # Add information about plots if they were generated
        if "plots" in result and result["plots"]:
            plot_paths = "\n".join(result["plots"])
            response_parts.append(f"Generated plots:\n{plot_paths}")
        
        # Join all parts with double newlines
        response_text = "\n\n".join(response_parts)
        
        # Return the formatted response
        return response_text
    except Exception as e:
        # Handle unexpected exceptions
        import traceback
        error_details = traceback.format_exc()
        return f"Error executing Python code: {str(e)}\n\nDetails:\n{error_details}"

@tool
def human_assistance(query: str) -> str:
    """
    Request expert input on complex scientific questions.
    
    Args:
        query: The scientific question or issue requiring human expertise
        
    Returns:
        Expert input provided by a human researcher
    """
    try:
        # This will pause execution and wait for human input
        response = interrupt({"query": query})
        return response["data"]
    except Exception as e:
        raise ToolException(f"Error getting human assistance: {str(e)}")