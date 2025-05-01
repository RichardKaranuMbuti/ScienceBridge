import os
import pandas as pd


def fetch_local_data(directory_path: str) -> dict:
    """
    Scans the directory (recursively) for CSV and Excel files, then returns
    a dictionary where each key is the file name, and the value is another
    dictionary with full path, column names, and number of records.
    
    Creates the directory if it doesn't exist.
    """
    # Create directory if it doesn't exist
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        print(f"Created directory: {os.path.abspath(directory_path)}")
    
    path = os.path.abspath(directory_path)
    print(f"Searching for files in: {path}")
    print(f"Directory contents: {os.listdir(path)}")
    data_summary = {}

    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(('.csv', '.xlsx', '.xls')):
                full_path = os.path.join(root, file)
                try:
                    if file.endswith('.csv'):
                        df = pd.read_csv(full_path)
                    else:
                        df = pd.read_excel(full_path)

                    data_summary[file] = {
                        'full_path': full_path,
                        'columns': df.columns.tolist(),
                        'num_records': len(df)
                    }
                except Exception as e:
                    data_summary[file] = {
                        'full_path': full_path,
                        'error': f"Failed to read file: {str(e)}"
                    }

    return data_summary