
from src.python_executor.simple_python_executor import SimplePythonExecutor


# Example code simple python executor
code = """
import os
import pandas as pd
import matplotlib.pyplot as plt

# Ensure charts directory exists
os.makedirs('charts', exist_ok=True)

# Create sample data
data = {'Category': ['A', 'B', 'C', 'D'], 'Values': [10, 25, 15, 30]}
df = pd.DataFrame(data)

# Generate a bar plot
plt.figure(figsize=(10, 6))
plt.bar(df['Category'], df['Values'])
plt.title('Sample Bar Chart')

# Save the plot to charts/sample_plot.png
plt.savefig('charts/sample_plot.png')

print("Analysis complete! Chart saved to charts/sample_plot.png")
"""



def main():
    # Initialize the executor with default packages
    executor = SimplePythonExecutor()
    
    # Install an additional package
    print("Installing 'requests' package...")
    # result = executor.install_package("requests")
    print(f"Package installation result: {result['success']}")
    
    
    # Execute a simple data analysis script
    print("\nExecuting sample data analysis code...")
    
    # Execute the code
    result = executor.execute_code(code)
    
    # Print execution results
    if result['success']:
        print("\nCode executed successfully!")
        print("\nStandard output:")
        print(result['stdout'])
        
        if 'plots' in result and result['plots']:
            print(f"\nGenerated {len(result['plots'])} plots saved at:")
            for plot_file in result['plots']:
                print(f"  - {plot_file}")
    else:
        print("\nCode execution failed!")
        print("\nError output:")
        print(result['stderr'])

if __name__ == "__main__":
    main()