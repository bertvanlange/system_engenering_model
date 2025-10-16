import pandas as pd
import os
from pathlib import Path

# Define the base directory and output directory
base_dir = Path(__file__).parent  # solar_power_data directory
output_dir = base_dir / "filtered_solar_data"

# Create output directory if it doesn't exist
output_dir.mkdir(exist_ok=True)

# Get all subdirectories in solar_power_data (monthly folders)
monthly_folders = [f for f in base_dir.iterdir() if f.is_dir() and f.name.endswith("_solar")]

print(f"Found {len(monthly_folders)} monthly folders to process\n")

# Process each monthly folder
total_files_processed = 0
for month_folder in sorted(monthly_folders):
    print(f"Processing folder: {month_folder.name}")
    
    # Create corresponding output subfolder
    output_subfolder = output_dir / month_folder.name
    output_subfolder.mkdir(exist_ok=True)
    
    # Get all CSV files in the monthly folder
    csv_files = list(month_folder.glob("*.csv"))
    
    for csv_file in csv_files:
        try:
            # Load the dataset
            df = pd.read_csv(csv_file)
            
            # Convert interval_start_local to datetime (if it isn't already)
            if "interval_start_local" in df.columns:
                df["interval_start_local"] = pd.to_datetime(df["interval_start_local"])
                
                # Drop duplicate timestamps, keeping only the first occurrence
                df_unique = df.drop_duplicates(subset=["interval_start_local"], keep="first")
                
                # Sort by time
                df_unique = df_unique.sort_values("interval_start_local").reset_index(drop=True)
                
                # Save the cleaned dataset
                output_file = output_subfolder / csv_file.name
                df_unique.to_csv(output_file, index=False)
                
                print(f"  [OK] {csv_file.name}: {len(df)} -> {len(df_unique)} rows (removed {len(df) - len(df_unique)} duplicates)")
                total_files_processed += 1
            else:
                print(f"  [SKIP] {csv_file.name}: No 'interval_start_local' column found, skipping")
                
        except Exception as e:
            print(f"  [ERROR] Error processing {csv_file.name}: {str(e)}")
    
    print()  # Empty line between folders

print(f"Processing complete! {total_files_processed} files filtered and saved to {output_dir}")
print("\n" + "="*80)
print("COMBINING ALL FILTERED FILES INTO ONE DATASET")
print("="*80 + "\n")

# Combine all filtered files
all_data = []
for month_folder in sorted(monthly_folders):
    output_subfolder = output_dir / month_folder.name
    csv_files = list(output_subfolder.glob("*.csv"))
    
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        df["interval_start_local"] = pd.to_datetime(df["interval_start_local"])
        all_data.append(df)
        print(f"Added {month_folder.name}/{csv_file.name}: {len(df)} rows")

# Combine all dataframes
combined_df = pd.concat(all_data, ignore_index=True)
combined_df = combined_df.sort_values("interval_start_local").reset_index(drop=True)

print(f"\nTotal combined rows: {len(combined_df)}")

# Save combined dataset
combined_output = base_dir / "solar_data_combined.csv"
combined_df.to_csv(combined_output, index=False)
print(f"Combined data saved to: {combined_output}")

# Analyze missing hours
print("\n" + "="*80)
print("ANALYZING MISSING HOURS")
print("="*80 + "\n")

# Get the first and last timestamp
first_timestamp = combined_df["interval_start_local"].min()
last_timestamp = combined_df["interval_start_local"].max()

print(f"Data range: {first_timestamp} to {last_timestamp}")
print(f"Total period: {(last_timestamp - first_timestamp).days} days")

# Create a complete hourly range
expected_range = pd.date_range(start=first_timestamp, end=last_timestamp, freq='h')
print(f"Expected hours: {len(expected_range)}")
print(f"Actual hours: {len(combined_df)}")

# Find missing timestamps
actual_timestamps = set(combined_df["interval_start_local"])
missing_timestamps = sorted([ts for ts in expected_range if ts not in actual_timestamps])

print(f"\nMissing hours: {len(missing_timestamps)}")

if len(missing_timestamps) > 0:
    print(f"\nFirst 20 missing timestamps:")
    for i, ts in enumerate(missing_timestamps[:20]):
        print(f"  {i+1}. {ts}")
    
    if len(missing_timestamps) > 20:
        print(f"  ... and {len(missing_timestamps) - 20} more")
    
    # Find gaps (consecutive missing hours)
    print("\n" + "-"*80)
    print("GAPS IN DATA (consecutive missing hours):")
    print("-"*80)
    
    gaps = []
    if missing_timestamps:
        gap_start = missing_timestamps[0]
        gap_end = missing_timestamps[0]
        
        for i in range(1, len(missing_timestamps)):
            if (missing_timestamps[i] - missing_timestamps[i-1]).total_seconds() == 3600:
                gap_end = missing_timestamps[i]
            else:
                gaps.append((gap_start, gap_end, (gap_end - gap_start).total_seconds() / 3600 + 1))
                gap_start = missing_timestamps[i]
                gap_end = missing_timestamps[i]
        
        gaps.append((gap_start, gap_end, (gap_end - gap_start).total_seconds() / 3600 + 1))
    
    print(f"\nFound {len(gaps)} gap(s):\n")
    for i, (start, end, hours) in enumerate(gaps, 1):
        print(f"{i}. {start} to {end} ({int(hours)} hour(s) missing)")
    
    # Save missing timestamps to file
    missing_df = pd.DataFrame({"missing_timestamp": missing_timestamps})
    missing_output = base_dir / "missing_timestamps.csv"
    missing_df.to_csv(missing_output, index=False)
    print(f"\nMissing timestamps saved to: {missing_output}")
else:
    print("\nNo missing hours! Data is complete. ✓")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)