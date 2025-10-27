import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Path to the dataset folder
dataset_folder = "Dataset on Hourly Load Profiles for 24 Facilities (8760 hours)"

# List all CSV files in the folder
files = [f for f in os.listdir(dataset_folder) if f.endswith('.csv')]

for file in files:
    file_path = os.path.join(dataset_folder, file)
    # Try to read the CSV file
    try:
        df = pd.read_csv(file_path, parse_dates=True)
    except Exception as e:
        print(f"Could not read {file}: {e}")
        continue

    # Try to find a datetime column
    datetime_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            datetime_col = col
            break

    if datetime_col:
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        df = df.set_index(datetime_col)
    else:
        df.index = pd.RangeIndex(len(df))

    # Plot numeric columns only
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        print(f"Skipping {file}: no numeric columns to plot")
        continue
    ax = numeric.plot(title=f"{file} - {df.index[0] if len(df) > 0 else ''}")
    plt.xlabel('Datetime' if datetime_col else 'Index')
    plt.ylabel('Value')
    plt.tight_layout()
    base_name = os.path.splitext(file)[0]
    image_png = base_name + ".png"
    image_svg = base_name + ".svg"
    image_eps = base_name + ".eps"
    plt.savefig(image_png, dpi=150, bbox_inches='tight')
    try:
        plt.savefig(image_svg, format='svg', bbox_inches='tight')
    except Exception:
        print(f"Failed to save SVG for {image_svg}")
    try:
        plt.savefig(image_eps, format='eps', bbox_inches='tight')
    except Exception:
        print(f"Failed to save EPS for {image_eps} (PostScript backend may not support transparency)")
    plt.close()