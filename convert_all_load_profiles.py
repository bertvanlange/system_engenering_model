"""
Convert all load profile CSVs from the Dataset on Hourly Load Profiles folder
to the simulation input format: hour,load_kw
Saves converted files to input_data/load_profiles/
"""
import os
from pathlib import Path
import pandas as pd

def convert_load_profile(input_path, output_path):
    """Convert a single load profile to hour,load_kw format."""
    try:
        df = pd.read_csv(input_path, header=0)
        # If the first column is not numeric, drop it (could be a timestamp or index)
        if not pd.api.types.is_numeric_dtype(df.iloc[:,0]):
            df = df.iloc[:, 1:]
        # Use the first column as load
        load = df.iloc[:,0].values
        out = pd.DataFrame({
            'hour': range(len(load)),
            'load_kw': load
        })
        out.to_csv(output_path, index=False)
        return True
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

# Source and destination folders
source_folder = Path("Dataset on Hourly Load Profiles for 24 Facilities (8760 hours)")
dest_folder = Path("input_data/load_profiles")

# Create destination folder if it doesn't exist
dest_folder.mkdir(parents=True, exist_ok=True)

# Convert all CSV files in the source folder
csv_files = list(source_folder.glob("*.csv"))
print(f"Found {len(csv_files)} CSV files in {source_folder}")
print(f"Converting to {dest_folder}...\n")

success_count = 0
for csv_file in csv_files:
    # Create output filename (sanitize the name)
    output_name = csv_file.stem.replace(" ", "_").replace("-", "_") + ".csv"
    output_path = dest_folder / output_name
    
    print(f"Converting: {csv_file.name} -> {output_name}")
    if convert_load_profile(csv_file, output_path):
        success_count += 1

print(f"\n✓ Successfully converted {success_count}/{len(csv_files)} files")
print(f"Output location: {dest_folder.absolute()}")
