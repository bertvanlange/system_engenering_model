import os
import pandas as pd
import matplotlib.pyplot as plt

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

    # Plot all columns except the index
    ax = df.plot(title=f"{file} - {df.index[0] if len(df) > 0 else ''}")
    plt.xlabel('Datetime' if datetime_col else 'Index')
    plt.ylabel('Value')
    plt.tight_layout()
    image_filename = os.path.splitext(file)[0] + ".png"
    plt.savefig(image_filename)
    plt.show(block=False)
    plt.pause(0.1)