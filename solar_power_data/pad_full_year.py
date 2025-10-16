import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("PADDING SOLAR DATA TO CREATE FULL YEAR")
print("="*80)

# Load the combined data
base_dir = Path(__file__).parent
combined_file = base_dir / "solar_data_combined.csv"

print(f"\nLoading combined data from: {combined_file.name}")
df = pd.read_csv(combined_file)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df = df.sort_values('interval_start_local').reset_index(drop=True)

print(f"Original data: {len(df)} hours")
print(f"Date range: {df['interval_start_local'].min()} to {df['interval_start_local'].max()}")

# Define the full year range
start_date = pd.Timestamp('2024-01-01 00:00:00', tz=df['interval_start_local'].iloc[0].tz)
end_date = pd.Timestamp('2024-12-31 23:00:00', tz=df['interval_start_local'].iloc[0].tz)

print(f"\nTarget range: {start_date} to {end_date}")

# Create full hourly range for the entire year (already has timezone from start_date)
full_range = pd.date_range(start=start_date, end=end_date, freq='h')
print(f"Target hours: {len(full_range)}")

print("\n" + "-"*80)
print("PADDING STRATEGY:")
print("-"*80)
print("For each missing hour, we'll use data from the same hour on the last")
print("available day. This preserves the daily solar pattern (day/night cycle).")
print("-"*80)

# Create a dataframe with all hours
padded_df = pd.DataFrame({'interval_start_local': full_range})

# Merge with existing data
padded_df = padded_df.merge(df, on='interval_start_local', how='left')

# Get column names (excluding timestamp columns)
data_columns = [col for col in df.columns if col != 'interval_start_local' and 
                not col.endswith('_utc') and not col.startswith('interval_end') and 
                not col.startswith('publish_time')]

print(f"\nData columns to pad: {data_columns}")

# For each missing hour, find the same hour from the most recent available day
print("\nPadding missing hours...")
missing_mask = padded_df[data_columns[0]].isna()
missing_count = missing_mask.sum()
print(f"Missing hours to pad: {missing_count}")

# Group existing data by hour of day to create a typical daily pattern
df['hour_of_day'] = df['interval_start_local'].dt.hour

# Calculate average values for each hour of the day
hourly_pattern = df.groupby('hour_of_day')[data_columns].mean()

print("\nCalculated average hourly pattern from available data:")
print(hourly_pattern)

# Fill missing values using the hourly pattern
print("\nApplying hourly pattern to missing data...")
for idx in padded_df[missing_mask].index:
    hour = padded_df.loc[idx, 'interval_start_local'].hour
    for col in data_columns:
        if col in hourly_pattern.columns:
            padded_df.loc[idx, col] = hourly_pattern.loc[hour, col]

# Add back the timestamp columns with proper values
padded_df['interval_end_local'] = padded_df['interval_start_local'] + pd.Timedelta(hours=1)

# Convert to UTC (assuming the timezone from original data)
if 'interval_start_utc' in df.columns:
    padded_df['interval_start_utc'] = padded_df['interval_start_local'].dt.tz_convert('UTC')
    padded_df['interval_end_utc'] = padded_df['interval_end_local'].dt.tz_convert('UTC')

print(f"\nPadded data: {len(padded_df)} hours")
print(f"Date range: {padded_df['interval_start_local'].min()} to {padded_df['interval_start_local'].max()}")

# Check for any remaining missing values
missing_after = padded_df[data_columns].isna().sum().sum()
print(f"Remaining missing values: {missing_after}")

# Save the padded dataset
output_file = base_dir / "solar_data_full_year_padded.csv"
padded_df.to_csv(output_file, index=False)
print(f"\n✓ Full year data saved to: {output_file.name}")

# Statistics
print("\n" + "="*80)
print("STATISTICS:")
print("="*80)
print(f"Original hours: {len(df)}")
print(f"Padded hours: {missing_count}")
print(f"Total hours: {len(padded_df)}")
print(f"Data completeness: {(len(df) / len(padded_df) * 100):.1f}% original, {(missing_count / len(padded_df) * 100):.1f}% padded")

# Show sample of padded data
print("\n" + "-"*80)
print("SAMPLE OF PADDED DATA (Jan 14-15, which were missing):")
print("-"*80)
sample = padded_df[(padded_df['interval_start_local'] >= '2024-01-14 00:00:00') & 
                    (padded_df['interval_start_local'] <= '2024-01-15 05:00:00')]
print(sample[['interval_start_local'] + data_columns].head(10).to_string())

print("\n" + "="*80)
print("PADDING COMPLETE!")
print("="*80)
