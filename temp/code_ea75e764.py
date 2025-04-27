import pandas as pd

# Load the datasets
compounds_descriptors = pd.read_csv('src/data/compounds_descriptors.csv')
experiment_metadata = pd.read_csv('src/data/experiment_metadata.csv')

# Merge datasets on compound_id
merged_data = pd.merge(compounds_descriptors, experiment_metadata, on='compound_id')

# Analyze the relationship between pH, temperature, exposure time, and bioactivity
# Group by logP and calculate mean bioactivity for different experimental conditions
results = merged_data.groupby(['logP', 'experiment_temp', 'pH', 'exposure_time_hr'])['bioactivity'].mean().reset_index()

# Find the combination of pH, temperature, and exposure time that maximizes bioactivity for each logP
optimal_conditions = results.loc[results.groupby('logP')['bioactivity'].idxmax()]

# Analyze optimal experimental windows for different molecular weight ranges
mol_weight_bins = pd.cut(merged_data['mol_weight'], bins=[0, 300, 500, 700, 1000], include_lowest=True)
merged_data['mol_weight_bin'] = mol_weight_bins
weight_results = merged_data.groupby(['mol_weight_bin', 'experiment_temp', 'pH', 'exposure_time_hr'])['bioactivity'].mean().reset_index()

# Find the optimal conditions for each molecular weight range
optimal_weight_conditions = weight_results.loc[weight_results.groupby('mol_weight_bin')['bioactivity'].idxmax()]

# Convert results to dictionaries for output
optimal_conditions_dict = optimal_conditions.to_dict('records')
optimal_weight_conditions_dict = optimal_weight_conditions.to_dict('records')

optimal_conditions_dict, optimal_weight_conditions_dict