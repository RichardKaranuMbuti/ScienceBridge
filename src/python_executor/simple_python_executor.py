import os
import sys
import subprocess
import venv
import tempfile
import traceback
from pathlib import Path
from typing import List, Optional, Union, Dict, Any

class SimplePythonExecutor:
    """
    A simple tool for AI agents to execute Python code in an isolated virtual environment.
    Handles setup, package management, and code execution with output capture.
    """
    
    def __init__(
        self, 
        venv_path: Optional[str] = None,
        packages: Optional[List[str]] = None,
        auto_install: bool = True
    ):
        """
        Initialize the Python executor with a virtual environment.
        
        Args:
            venv_path: Path to the virtual environment. If None, a default path will be used.
            packages: Additional packages to install beyond the defaults.
            auto_install: Whether to automatically install packages during initialization.
        """
        # Default packages if none provided
        self.default_packages = [
            "numpy", "pandas", "matplotlib", "seaborn", 
            "scikit-learn", "plotly", "statsmodels"
        ]
        
        # Set virtual environment path relative to the current directory
        self.venv_path = venv_path or os.path.join(os.getcwd(), "venvs")
        self.python_path = self._get_python_path()
        self.pip_path = self._get_pip_path()
        
        # Combine default and additional packages
        self.packages = self.default_packages.copy()
        if packages:
            self.packages.extend([pkg for pkg in packages if pkg not in self.packages])
        
        # Initialize virtual environment if it doesn't exist
        if not os.path.exists(self.venv_path):
            self._create_venv()
            if auto_install:
                self.install_packages(self.packages)
        elif auto_install:
            # Check if we need to install any packages
            self.install_packages(self.packages)
        
        # Temp directory for code execution
        self.temp_dir = tempfile.mkdtemp(prefix="ai_agent_exec_")
        
    def _get_python_path(self) -> str:
        """Get the path to the Python executable in the virtual environment."""
        if os.name == 'nt':  # Windows
            return os.path.join(self.venv_path, 'Scripts', 'python.exe')
        else:  # Unix/Linux/Mac
            return os.path.join(self.venv_path, 'bin', 'python')
    
    def _get_pip_path(self) -> str:
        """Get the path to the pip executable in the virtual environment."""
        if os.name == 'nt':  # Windows
            return os.path.join(self.venv_path, 'Scripts', 'pip.exe')
        else:  # Unix/Linux/Mac
            return os.path.join(self.venv_path, 'bin', 'pip')
    
    def _create_venv(self) -> None:
        """Create a new virtual environment."""
        print(f"Creating virtual environment at {self.venv_path}")
        os.makedirs(os.path.dirname(self.venv_path), exist_ok=True)
        venv.create(self.venv_path, with_pip=True)
        
    def install_package(self, package: str) -> Dict[str, Any]:
        """
        Install a single package in the virtual environment.
        
        Args:
            package: The name of the package to install.
            
        Returns:
            Dict containing success status and output/error messages.
        """
        return self.install_packages([package])
    
    def install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """
        Install multiple packages in the virtual environment.
        
        Args:
            packages: List of package names to install.
            
        Returns:
            Dict containing success status and output/error messages.
        """
        if not packages:
            return {"success": True, "message": "No packages specified for installation."}
        
        try:
            cmd = [self.pip_path, "install"] + packages
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully installed packages: {', '.join(packages)}",
                    "output": process.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to install packages: {', '.join(packages)}",
                    "error": process.stderr
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Exception during package installation: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def uninstall_package(self, package: str) -> Dict[str, Any]:
        """
        Uninstall a package from the virtual environment.
        
        Args:
            package: The name of the package to uninstall.
            
        Returns:
            Dict containing success status and output/error messages.
        """
        try:
            cmd = [self.pip_path, "uninstall", "-y", package]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Successfully uninstalled package: {package}",
                    "output": process.stdout
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to uninstall package: {package}",
                    "error": process.stderr
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Exception during package uninstallation: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def list_installed_packages(self) -> Dict[str, Any]:
        """
        List all installed packages in the virtual environment.
        
        Returns:
            Dict containing success status and list of installed packages.
        """
        try:
            cmd = [self.pip_path, "list"]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                # Parse package info from pip list output
                lines = process.stdout.strip().split('\n')[2:]  # Skip header lines
                packages = []
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append({"name": parts[0], "version": parts[1]})
                
                return {
                    "success": True,
                    "packages": packages,
                    "output": process.stdout
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to list installed packages",
                    "error": process.stderr
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Exception while listing packages: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def reset_venv(self) -> Dict[str, Any]:
        """
        Remove and recreate the virtual environment.
        Useful if the environment becomes corrupted.
        
        Returns:
            Dict containing success status and messages.
        """
        import shutil
        
        try:
            # Remove the existing virtual environment
            if os.path.exists(self.venv_path):
                shutil.rmtree(self.venv_path)
            
            # Create a new virtual environment
            self._create_venv()
            
            # Reinstall packages
            install_result = self.install_packages(self.packages)
            
            return {
                "success": True,
                "message": "Virtual environment reset successfully",
                "install_result": install_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to reset virtual environment: {str(e)}",
                "error": traceback.format_exc()
            }
    
    def execute_code(self, code: str, capture_plots: bool = True) -> Dict[str, Any]:
        """
        Execute Python code in the virtual environment.
        
        Args:
            code: String containing Python code to execute.
            capture_plots: Whether to capture matplotlib plots as images.
            
        Returns:
            Dict containing execution results, stdout/stderr, and any captured plots.
        """
        # Create a temporary file for the code
        code_file = os.path.join(self.temp_dir, "agent_code.py")
        
        # Handle matplotlib plots if requested
        if capture_plots:
            # Modify code to save plots
            plot_dir = os.path.join(self.temp_dir, "plots")
            os.makedirs(plot_dir, exist_ok=True)
            
            plot_save_code = f"""
                    import matplotlib.pyplot as plt
                    import os

                    # Store the original plt.show function
                    _original_show = plt.show

                    # Counter for plot figures
                    _figure_count = 0

                    # Override plt.show to save figures
                    def _custom_show(*args, **kwargs):
                        global _figure_count
                        # Save the current figure
                        plot_path = os.path.join(r"{plot_dir}", f"plot_{{_figure_count}}.png")
                        plt.savefig(plot_path)
                        _figure_count += 1
                        # Call the original show function
                        return _original_show(*args, **kwargs)

                    # Replace plt.show with our custom function
                    plt.show = _custom_show
                    """
                                # Add the plot saving code at the beginning
            code = plot_save_code + "\n" + code
        
        # Write code to file
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            # Execute the code using the virtual environment's Python
            cmd = [self.python_path, code_file]
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            result = {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "return_code": process.returncode
            }
            
            # Collect plots if any were saved
            if capture_plots:
                plot_files = []
                plot_dir = os.path.join(self.temp_dir, "plots")
                if os.path.exists(plot_dir):
                    plot_files = [os.path.join(plot_dir, f) for f in os.listdir(plot_dir) 
                                 if f.startswith("plot_") and f.endswith(".png")]
                    plot_files.sort(key=lambda x: int(x.split("plot_")[1].split(".png")[0]))
                
                result["plots"] = plot_files
                if plot_files:
                    result["plot_count"] = len(plot_files)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def cleanup(self):
        """Clean up temporary files created during execution."""
        # Don't import inside this method as it may be called during shutdown
        if os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except ImportError:
                # Fallback if shutil can't be imported during shutdown
                try:
                    for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(self.temp_dir)
                except Exception as e:
                    print(f"Warning: Failed to clean up temporary directory: {str(e)}")
            except Exception as e:
                print(f"Warning: Failed to clean up temporary directory: {str(e)}")

    def __del__(self):
        """Destructor to ensure cleanup when the object is garbage collected."""
        self.cleanup()
