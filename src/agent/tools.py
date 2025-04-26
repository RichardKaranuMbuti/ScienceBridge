from langchain_core.tools import tool
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
        The output of the code execution
    """
    try:
        # Create a local namespace for execution
        local_namespace = {"pd": pd, "plt": plt, "sns": sns}
        
        # Set non-interactive backend for matplotlib
        plt.switch_backend('Agg')
        
        # Create directory for plots if it doesn't exist
        os.makedirs("plots", exist_ok=True)
        
        # Capture stdout
        import io
        from contextlib import redirect_stdout
        
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            # Execute the code
            exec(code, globals(), local_namespace)
            
            # Save any matplotlib figures that were created
            plot_files = []
            for i, fig in enumerate(plt.get_fignums()):
                figure = plt.figure(fig)
                plot_path = f"plots/figure_{i}.png"
                figure.savefig(plot_path)
                plot_files.append(plot_path)
        
        # Get the captured stdout
        stdout_output = stdout_capture.getvalue()
        
        # Build the response
        response = []
        if stdout_output:
            response.append(f"Output:\n{stdout_output}")
        
        if plot_files:
            response.append(f"Generated plots: {', '.join(plot_files)}")
        
        # Check for return values in the local namespace
        result_vars = [f"{k} = {v}" for k, v in local_namespace.items() 
                     if k not in ["pd", "plt", "sns"] and not k.startswith("_")]
        
        if result_vars:
            response.append("Variables defined:\n" + "\n".join(result_vars[:5]))
            
        return "\n\n".join(response) or "Code executed successfully with no output."
    except Exception as e:
        import traceback
        return f"Error executing Python code:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
    
    