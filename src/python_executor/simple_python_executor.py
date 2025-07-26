#src/python_executor/simple_python_executor.py
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
        plots_dir: str = "plots",
        clear_plots_on_init: bool = False,
        use_system_python: bool = False
    ):
        """
        Initialize the Python executor with a virtual environment.
        
        Args:
            venv_path: Path to the virtual environment. If None, a default path will be used.
            packages: Additional packages to install beyond the defaults.
            auto_install: Whether to automatically install packages during initialization.
            plots_dir: Directory to save generated plots
            clear_plots_on_init: Whether to clear all plots when initializing
            use_system_python: If True, use system Python instead of venv (useful for Docker)
        """
        # Set default venv path if not provided
        self.venv_path = venv_path or os.path.join(os.getcwd(), "venvs")
        self.plots_dir = plots_dir
        self.use_system_python = use_system_python
        
        # Detect if we're in a Docker container
        self._detect_docker_environment()
        
        # Make sure plots directory exists
        os.makedirs(self.plots_dir, exist_ok=True)
        
        # Clear plots if requested
        if clear_plots_on_init:
            self.clear_plots_directory()
        
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
        if not self.use_system_python:
            self._setup_venv()
        
        # Install packages if auto_install is True
        if auto_install:
            self.install_packages(self.packages)
    
    def _detect_docker_environment(self):
        """Detect if we're running in a Docker container and adjust settings accordingly."""
        # Check for common Docker indicators
        docker_indicators = [
            os.path.exists('/.dockerenv'),
            os.path.exists('/proc/1/cgroup') and any('docker' in line for line in open('/proc/1/cgroup').readlines() if line.strip()),
            os.environ.get('DOCKER_CONTAINER') == 'true'
        ]
        
        is_docker = any(docker_indicators)
        
        if is_docker:
            print("Docker environment detected. Using system Python instead of virtual environment.")
            self.use_system_python = True
        
        return is_docker
    
    def _setup_venv(self) -> None:
        """Set up the virtual environment if it doesn't exist."""
        if self.use_system_python:
            print("Using system Python environment")
            return
            
        try:
            if not os.path.exists(self.venv_path):
                print(f"Creating virtual environment at {self.venv_path}")
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(self.venv_path), exist_ok=True)
                
                # Try to create the virtual environment
                venv.create(self.venv_path, with_pip=True, clear=True)
                
                # Verify the virtual environment was created successfully
                if not self._verify_venv():
                    print("Virtual environment creation failed, falling back to system Python")
                    self.use_system_python = True
            else:
                print(f"Using existing virtual environment at {self.venv_path}")
                if not self._verify_venv():
                    print("Existing virtual environment is invalid, recreating...")
                    shutil.rmtree(self.venv_path)
                    venv.create(self.venv_path, with_pip=True, clear=True)
                    
                    if not self._verify_venv():
                        print("Virtual environment recreation failed, falling back to system Python")
                        self.use_system_python = True
        except Exception as e:
            print(f"Error setting up virtual environment: {str(e)}")
            print("Falling back to system Python")
            self.use_system_python = True
    
    def _verify_venv(self) -> bool:
        """Verify that the virtual environment is properly set up."""
        if self.use_system_python:
            return True
            
        pip_path = self._get_pip_path()
        python_path = self._get_python_path()
        
        return os.path.exists(pip_path) and os.path.exists(python_path)
    
    def _get_pip_path(self) -> str:
        """Get the path to pip in the virtual environment or system."""
        if self.use_system_python:
            # Use system pip
            return "pip" if shutil.which("pip") else "pip3"
        
        # Use virtual environment pip
        if sys.platform == "win32":
            return os.path.join(self.venv_path, "Scripts", "pip.exe")
        else:
            return os.path.join(self.venv_path, "bin", "pip")
    
    def _get_python_path(self) -> str:
        """Get the path to python in the virtual environment or system."""
        if self.use_system_python:
            # Use current Python interpreter
            return sys.executable
        
        # Use virtual environment python
        if sys.platform == "win32":
            return os.path.join(self.venv_path, "Scripts", "python.exe")
        else:
            return os.path.join(self.venv_path, "bin", "python")
    
    def install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """
        Install Python packages in the virtual environment or system.
        
        Args:
            packages: List of package names to install
            
        Returns:
            Dict with success status and output/error message
        """
        if not packages:
            return {"success": True, "message": "No packages to install"}
        
        pip_path = self._get_pip_path()
        
        try:
            # Check which packages are already installed
            installed_packages = self._get_installed_packages()
            packages_to_install = [pkg for pkg in packages if pkg.lower() not in installed_packages]
            
            if not packages_to_install:
                return {
                    "success": True,
                    "message": f"All packages already installed: {', '.join(packages)}",
                    "output": "No new packages to install"
                }
            
            # Run pip install for the specified packages
            cmd = [pip_path, "install", "--upgrade"] + packages_to_install
            
            print(f"Installing packages: {', '.join(packages_to_install)}")
            print(f"Using pip at: {pip_path}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Installed packages: {', '.join(packages_to_install)}",
                    "output": process.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to install packages: {process.stderr}",
                    "error": process.stderr
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "Package installation timed out",
                "error": "Installation process exceeded 5 minute timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error installing packages: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def _get_installed_packages(self) -> set:
        """Get a set of currently installed package names."""
        try:
            pip_path = self._get_pip_path()
            result = subprocess.run(
                [pip_path, "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )
            
            if result.returncode == 0:
                installed = set()
                for line in result.stdout.strip().split('\n'):
                    if '==' in line:
                        package_name = line.split('==')[0].lower()
                        installed.add(package_name)
                return installed
            else:
                print(f"Warning: Could not get installed packages list: {result.stderr}")
                return set()
        except Exception as e:
            print(f"Warning: Error getting installed packages: {str(e)}")
            return set()
    
    def clear_plots_directory(self, specific_exec_id: Optional[str] = None):
        """
        Clear plots from the plots directory.
        
        Args:
            specific_exec_id: If provided, only clear the subfolder for this execution ID.
                             If None, clear all plots.
        
        Returns:
            Dict with success status and message
        """
        try:
            if specific_exec_id:
                # Clear only a specific execution folder
                exec_path = os.path.join(self.plots_dir, specific_exec_id)
                if os.path.exists(exec_path):
                    shutil.rmtree(exec_path)
                    return {
                        "success": True,
                        "message": f"Cleared plots for execution ID: {specific_exec_id}"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No plots directory found for execution ID: {specific_exec_id}"
                    }
            else:
                # Clear all plots by removing and recreating the directory
                if os.path.exists(self.plots_dir):
                    shutil.rmtree(self.plots_dir)
                    os.makedirs(self.plots_dir, exist_ok=True)
                    return {
                        "success": True,
                        "message": f"Cleared all plots from {self.plots_dir}"
                    }
                else:
                    os.makedirs(self.plots_dir, exist_ok=True)
                    return {
                        "success": True,
                        "message": f"Plots directory {self.plots_dir} was already empty"
                    }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clearing plots directory: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def execute_code(self, code: str, clear_previous_plots: bool = True) -> Dict[str, Any]:
        """
        Execute Python code in the virtual environment or system Python.
        
        Args:
            code: Python code to execute
            clear_previous_plots: Whether to clear all plots before execution
            
        Returns:
            Dict with execution results, including stdout, stderr, and plot paths
        """
        # Clear all previous plots if requested
        if clear_previous_plots:
            self.clear_plots_directory()
            
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
            env = os.environ.copy()
            # Add any necessary environment variables
            env['MPLCONFIGDIR'] = '/tmp/matplotlib'
            
            process = subprocess.run(
                [python_path, code_file],
                capture_output=True,
                text=True,
                check=False,
                env=env,
                timeout=300  # 5 minute timeout
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
            
            # Clean up temporary files for this execution
            try:
                os.remove(code_file)
            except:
                pass
                
            # Clean up memory
            gc.collect()
            
            return result
        
        except subprocess.TimeoutExpired:
            # Clean up if there was a timeout
            try:
                os.remove(code_file)
                self.clear_plots_directory(specific_exec_id=exec_id)
            except:
                pass
                
            return {
                "success": False,
                "stdout": "",
                "stderr": "Code execution timed out after 5 minutes",
                "plot_paths": [],
                "execution_id": exec_id
            }
        except Exception as e:
            # Clean up if there was an error
            try:
                os.remove(code_file)
                # Also clean up the plot directory for this execution since it failed
                self.clear_plots_directory(specific_exec_id=exec_id)
            except:
                pass
                
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Error executing code: {str(e)}\n{traceback.format_exc()}",
                "plot_paths": [],
                "execution_id": exec_id
            }
    
    def cleanup(self, clear_plots=False):
        """
        Clean up resources and temporary files.
        
        Args:
            clear_plots: If True, also clear all plot directories
        """
        # Clean up temp files
        temp_dir = os.path.join(os.getcwd(), "temp")
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # Optionally clear plots directory
        if clear_plots:
            self.clear_plots_directory()
        
        # Clean up memory
        gc.collect()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup(clear_plots=False)  # Default to not clearing plots on destruction
        except:
            pass