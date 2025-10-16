"""
Convert a load profile CSV (from the Dataset on Hourly Load Profiles for 24 Facilities) to the input format:
hour,load_kw
Assumes the input file has 8760 rows (one per hour), with or without a header.
Usage:
    python convert_load_profile_to_input_format.py input_file.csv output_file.csv
"""
import sys
import pandas as pd

def convert_load_profile(input_path, output_path):
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
    print(f'Converted {input_path} to {output_path} (columns: hour, load_kw)')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_load_profile_to_input_format.py input_file.csv output_file.csv")
        sys.exit(1)
    convert_load_profile(sys.argv[1], sys.argv[2])