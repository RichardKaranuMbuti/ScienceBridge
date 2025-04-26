from langchain_core.tools import tool
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from typing import List, Optional
from src.python_executor.simple_python_executor import SimplePythonExecutor
from src.openai_tool.client import OpenAIClient

# Initialize the Python executor once
python_executor = SimplePythonExecutor(
    venv_path=os.path.join(os.getcwd(), "venvs"),
    auto_install=True
)

@tool
def fetch_dataset_info(dataset_path: str) -> str:
    """
    Fetch information about available datasets.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        Information about available datasets
    """
    try:
        datasets = {}
        for file in os.listdir(dataset_path):
            if file.endswith('.csv'):
                file_path = os.path.join(dataset_path, file)
                df = pd.read_csv(file_path)
                datasets[file] = {
                    'full_path': file_path,
                    'columns': list(df.columns),
                    'num_records': len(df)
                }
        return str(datasets)
    except Exception as e:
        return f"Error fetching dataset info: {str(e)}"

@tool
def db_query_tool(query: str) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    """
    try:
        # This is a placeholder for SQL execution functionality
        # For a real implementation, connect to your database here
        return f"SQL Query result for: {query}"
    except Exception as e:
        return f"Error executing query: {str(e)}"

@tool
def execute_python(code: str) -> str:
    """
    Execute Python code for data analysis and visualization.
    
    Args:
        code: Python code to execute (can include data analysis, visualization, etc.)
        
    Returns:
        The output of the code execution, including any generated plots
    """
    result = python_executor.execute_code(code)
    
    response_parts = []
    
    if result["success"]:
        if result["stdout"]:
            response_parts.append(f"Output:\n{result['stdout']}")
        
        if result["plot_paths"]:
            paths_str = "\n".join(result["plot_paths"])
            response_parts.append(f"Generated plots:\n{paths_str}")
        
        if not response_parts:
            response_parts.append("Code executed successfully with no output.")
    else:
        error_message = result["stderr"] or "Unknown error occurred during execution"
        response_parts.append(f"Error executing Python code:\n{error_message}")
    
    return "\n\n".join(response_parts)

@tool
def install_python_packages(packages: str) -> str:
    """
    Install Python packages in the execution environment.
    
    Args:
        packages: Comma-separated list of packages to install
        
    Returns:
        Result of the installation attempt
    """
    # Parse the packages string into a list
    package_list = [pkg.strip() for pkg in packages.split(",") if pkg.strip()]
    
    if not package_list:
        return "No packages specified for installation."
    
    result = python_executor.install_packages(package_list)
    
    if result["success"]:
        return f"Successfully installed packages: {', '.join(package_list)}"
    else:
        return f"Failed to install packages: {result.get('error', 'Unknown error')}"

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
        answer = OpenAIClient(question)
        return answer
    except Exception as e:
        return f"Error querying AI: {str(e)}"