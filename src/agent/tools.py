from typing import List, Optional, Annotated, Dict, Any
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState, InjectedStore
# Remove BaseStore import since we're not using it anymore
import pandas as pd
import os
import json
import traceback
from src.python_executor.simple_python_executor import SimplePythonExecutor
from src.openai_tool.client import OpenAIClient
from src.openai_tool.OpenAIVisionClient import OpenAIVisionClient

# Initialize the Python executor once for global use
python_executor = SimplePythonExecutor(
    venv_path=os.path.join(os.getcwd(), "venvs"),
    auto_install=True
)

# Status printing utility
def print_tool_execution(tool_name: str, status: str = "RUNNING", details: str = None):
    """Print tool execution status to the terminal."""
    status_colors = {
        "RUNNING": "\033[33m",  # Yellow
        "SUCCESS": "\033[32m",  # Green
        "ERROR": "\033[31m",    # Red
    }
    color = status_colors.get(status, "\033[0m")
    reset = "\033[0m"
    
    print(f"\n{color}[TOOL: {tool_name}] {status}{reset}")
    if details:
        if status == "ERROR":
            print(f"{color}{details}{reset}")
        else:
            print(details)

@tool
def fetch_dataset_info(
    dataset_path: str, 
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Fetch information about available datasets.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        Information about available datasets including file names, columns, and record counts
    """
    print_tool_execution("fetch_dataset_info", "RUNNING", f"Fetching dataset info from {dataset_path}")
    
    try:
        datasets = {}
        for file in os.listdir(dataset_path):
            if file.endswith('.csv'):
                file_path = os.path.join(dataset_path, file)
                df = pd.read_csv(file_path)
                
                # Get column info with data types and sample values
                column_info = {}
                for col in df.columns:
                    # Get data type and sample values
                    dtype = str(df[col].dtype)
                    sample = df[col].head(3).tolist()
                    column_info[col] = {
                        "dtype": dtype,
                        "sample": sample
                    }
                
                datasets[file] = {
                    'full_path': file_path,
                    'columns': list(df.columns),
                    'column_details': column_info,
                    'num_records': len(df),
                    'missing_values': df.isna().sum().to_dict()
                }
        
        result = json.dumps(datasets, indent=2)
        print_tool_execution("fetch_dataset_info", "SUCCESS")
        return result
    except Exception as e:
        error_trace = traceback.format_exc()
        print_tool_execution("fetch_dataset_info", "ERROR", error_trace)
        return f"Error fetching dataset info: {str(e)}\n{error_trace}"

@tool
def execute_python(
    code: str,
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Execute Python code for data analysis and visualization.
    
    Args:
        code: Python code to execute (can include data analysis, visualization, etc.)
        
    Returns:
        The output of the code execution, including any generated plots
    """
    print_tool_execution("execute_python", "RUNNING", f"Executing Python code...")
    
    result = python_executor.execute_code(code)
    
    response_parts = []
    
    if result["success"]:
        if result["stdout"]:
            response_parts.append(f"Output:\n{result['stdout']}")
        
        if result["plot_paths"]:
            paths_str = "\n".join(result["plot_paths"])
            response_parts.append(f"Generated plots:\n{paths_str}")
            
            # Store plot paths in the state if available
            if state is not None:
                if "plot_paths" not in state:
                    state["plot_paths"] = []
                state["plot_paths"].extend(result["plot_paths"])
        
        if not response_parts:
            response_parts.append("Code executed successfully with no output.")
            
        print_tool_execution("execute_python", "SUCCESS")
    else:
        error_message = result["stderr"] or "Unknown error occurred during execution"
        response_parts.append(f"Error executing Python code:\n{error_message}")
        print_tool_execution("execute_python", "ERROR", error_message)
    
    return "\n\n".join(response_parts)

@tool
def install_python_packages(
    packages: str,
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Install Python packages in the execution environment.
    
    Args:
        packages: Comma-separated list of packages to install
        
    Returns:
        Result of the installation attempt
    """
    print_tool_execution("install_python_packages", "RUNNING", f"Installing packages: {packages}")
    
    # Parse the packages string into a list
    package_list = [pkg.strip() for pkg in packages.split(",") if pkg.strip()]
    
    if not package_list:
        print_tool_execution("install_python_packages", "ERROR", "No packages specified")
        return "No packages specified for installation."
    
    result = python_executor.install_packages(package_list)
    
    if result["success"]:
        success_msg = f"Successfully installed packages: {', '.join(package_list)}"
        print_tool_execution("install_python_packages", "SUCCESS", success_msg)
        return success_msg
    else:
        error_msg = f"Failed to install packages: {result.get('error', 'Unknown error')}"
        print_tool_execution("install_python_packages", "ERROR", error_msg)
        return error_msg

@tool
def ask_ai(
    question: str,
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Query specialized knowledge sources about scientific concepts.
    
    Args:
        question: The scientific question to research
        
    Returns:
        Detailed information about the scientific concept
    """
    print_tool_execution("ask_ai", "RUNNING", f"Researching: {question}")
    
    try:
        # Use your existing OpenAIClient implementation
        answer = OpenAIClient(question)
        print_tool_execution("ask_ai", "SUCCESS")
        return answer
    except Exception as e:
        error_trace = traceback.format_exc()
        print_tool_execution("ask_ai", "ERROR", error_trace)
        return f"Error querying AI: {str(e)}\n{error_trace}"

@tool
def explain_graph(
    query: str, 
    image_paths: Optional[List[str]] = None,
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Explain the generated graph using AI vision capabilities.
    
    Args:
        query: Question about the graph you want explained
        image_paths: List of paths to image files (if not provided, will use latest from state)
        
    Returns:
        Detailed explanation of what's shown in the graph
    """
    print_tool_execution("explain_graph", "RUNNING", f"Analyzing graphs for: {query}")
    
    try:
        # If image paths not provided, check state for recent plots
        if not image_paths and state and "plot_paths" in state:
            image_paths = state["plot_paths"]
        
        if not image_paths:
            print_tool_execution("explain_graph", "ERROR", "No image paths provided or found in state")
            return "Error: No images to explain. Please generate plots first using execute_python."
        
        # Use your existing OpenAIVisionClient implementation
        explanation = OpenAIVisionClient(
            query=query,
            image_paths=image_paths,
            system_prompt="You are a helpful visual analysis assistant. Describe what you observe in the images with scientific precision. Analyze trends, patterns, outliers, and relationships between variables. Explain what scientific insights can be drawn from these visualizations."
        )
        
        if not explanation:
            print_tool_execution("explain_graph", "ERROR", "No explanation provided")
            return "No explanation provided."
        
        print_tool_execution("explain_graph", "SUCCESS")
        return explanation
    except Exception as e:
        error_trace = traceback.format_exc()
        print_tool_execution("explain_graph", "ERROR", error_trace)
        return f"Error explaining graph: {str(e)}\n{error_trace}"

@tool
def db_query_tool(
    query: str,
    state: Annotated[Dict, InjectedState] = None,
    store: Annotated[Any, InjectedStore()] = None,  # Changed from BaseStore to Any
    config: RunnableConfig = None
) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    
    Args:
        query: SQL query to execute
        
    Returns:
        Query results or error message
    """
    print_tool_execution("db_query_tool", "RUNNING", f"Executing SQL query")
    
    try:
        # This is a placeholder for SQL execution functionality
        # For a real implementation, connect to your database here
        result = f"SQL Query result for: {query}"
        print_tool_execution("db_query_tool", "SUCCESS")
        return result
    except Exception as e:
        error_trace = traceback.format_exc()
        print_tool_execution("db_query_tool", "ERROR", error_trace)
        return f"Error executing query: {str(e)}\n{error_trace}"