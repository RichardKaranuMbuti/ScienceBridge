# src/python_executor/simple_python_executor.py
import os
import sys
import venv
import subprocess
import io
import traceback
from typing import List, Optional, Dict, Any
from contextlib import redirect_stdout, redirect_stderr
import shutil
import matplotlib.pyplot as plt
import uuid
import gc

class SimplePythonExecutor:
    """
    A simple tool for AI agents to execute Python code in an isolated virtual environment.
    Handles setup, package management, and code execution with output capture.
    """
    
    def __init__(
        self, 
        venv_path: Optional[str] = None, 
        packages: Optional[List[str]] = None, 
        auto_install: bool = True,
        plots_dir: str = "plots"
    ):
        """
        Initialize the Python executor with a virtual environment.
        
        Args:
            venv_path: Path to the virtual environment. If None, a default path will be used.
            packages: Additional packages to install beyond the defaults.
            auto_install: Whether to automatically install packages during initialization.
            plots_dir: Directory to save generated plots
        """
        # Set default venv path if not provided
        self.venv_path = venv_path or os.path.join(os.getcwd(), "venvs")
        self.plots_dir = plots_dir
        
        # Make sure plots directory exists
        os.makedirs(self.plots_dir, exist_ok=True)
        
        # Default packages if none provided
        self.default_packages = [
            "numpy",
            "pandas",
            "matplotlib",
            "seaborn",
            "scikit-learn",
            "plotly",
            "statsmodels"
        ]
        
        # Combine default packages with additional packages
        self.packages = self.default_packages.copy()
        if packages:
            self.packages.extend(packages)
        
        # Create or verify the virtual environment
        self._setup_venv()
        
        # Install packages if auto_install is True
        if auto_install:
            self.install_packages(self.packages)
    
    def _setup_venv(self) -> None:
        """Set up the virtual environment if it doesn't exist."""
        if not os.path.exists(self.venv_path):
            print(f"Creating virtual environment at {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)
        else:
            print(f"Using existing virtual environment at {self.venv_path}")
    
    def _get_pip_path(self) -> str:
        """Get the path to pip in the virtual environment."""
        if sys.platform == "win32":
            return os.path.join(self.venv_path, "Scripts", "pip.exe")
        else:
            return os.path.join(self.venv_path, "bin", "pip")
    
    def _get_python_path(self) -> str:
        """Get the path to python in the virtual environment."""
        if sys.platform == "win32":
            return os.path.join(self.venv_path, "Scripts", "python.exe")
        else:
            return os.path.join(self.venv_path, "bin", "python")
    
    def install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """
        Install Python packages in the virtual environment.
        
        Args:
            packages: List of package names to install
            
        Returns:
            Dict with success status and output/error message
        """
        if not packages:
            return {"success": True, "message": "No packages to install"}
        
        pip_path = self._get_pip_path()
        
        try:
            # Run pip install for the specified packages
            cmd = [pip_path, "install"] + packages
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Installed packages: {', '.join(packages)}",
                    "output": process.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to install packages: {process.stderr}",
                    "error": process.stderr
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error installing packages: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Execute Python code in the virtual environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Dict with execution results, including stdout, stderr, and plot paths
        """
        python_path = self._get_python_path()
        
        # Generate a unique identifier for this execution
        exec_id = str(uuid.uuid4())[:8]
        
        # Create a temporary file to store the code
        temp_dir = os.path.join(os.getcwd(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        code_file = os.path.join(temp_dir, f"code_{exec_id}.py")
        
        # Add code to save any matplotlib figures
        plot_dir = os.path.join(self.plots_dir, exec_id)
        os.makedirs(plot_dir, exist_ok=True)
        
        # Modify the code to automatically save generated plots
        plot_saving_code = f"""
import matplotlib.pyplot as plt
import os

# Store original savefig function
original_savefig = plt.savefig

# Override savefig to keep track of saved files
saved_files = []

def custom_savefig(*args, **kwargs):
    # Call the original savefig
    result = original_savefig(*args, **kwargs)
    
    # Record the file path if it's a positional arg
    if args and isinstance(args[0], str):
        saved_files.append(args[0])
    # Record the file path if it's a keyword arg
    elif 'fname' in kwargs and isinstance(kwargs['fname'], str):
        saved_files.append(kwargs['fname'])
    
    return result

# Apply the custom savefig
plt.savefig = custom_savefig

# Store the original show function
original_show = plt.show

# Override show to save figures
def custom_show(*args, **kwargs):
    # Save all currently open figures
    for i, fig_num in enumerate(plt.get_fignums()):
        fig = plt.figure(fig_num)
        filename = os.path.join("{plot_dir}", f"figure_{{i}}.png")
        fig.savefig(filename)
        saved_files.append(filename)
    
    # Call the original show function
    return original_show(*args, **kwargs)

# Apply the custom show
plt.show = custom_show

# At the end of script execution, print out the saved files
def _print_saved_files():
    if saved_files:
        print("\\n--- GENERATED PLOTS ---")
        for f in saved_files:
            print(f)

import atexit
atexit.register(_print_saved_files)
"""
        
        # Add the plot saving code at the beginning
        modified_code = plot_saving_code + "\n\n" + code
        
        # Write the code to the temporary file
        with open(code_file, "w") as f:
            f.write(modified_code)
        
        try:
            # Execute the code
            process = subprocess.run(
                [python_path, code_file],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse the output to extract plot paths
            stdout = process.stdout
            plot_paths = []
            
            # Look for the plot paths in the output
            if "--- GENERATED PLOTS ---" in stdout:
                plot_section = stdout.split("--- GENERATED PLOTS ---")[1].strip()
                plot_paths = [line.strip() for line in plot_section.split("\n") if line.strip()]
                
                # Remove the plot section from the output
                stdout = stdout.split("--- GENERATED PLOTS ---")[0].strip()
            
            result = {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": process.stderr,
                "plot_paths": plot_paths,
                "execution_id": exec_id
            }
            
            # Clean up memory
            gc.collect()
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error executing code: {str(e)}\n{traceback.format_exc()}",
                "plot_paths": [],
                "execution_id": exec_id
            }
        finally:
            # Clean up the temporary file
            try:
                os.remove(code_file)
            except:
                pass
    
    def cleanup(self):
        """Clean up resources and temporary files."""
        # This method could be extended to clean up temp files, etc.
        pass
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
        gc.collect()