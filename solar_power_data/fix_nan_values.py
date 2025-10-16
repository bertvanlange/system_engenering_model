import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("FIXING REMAINING NaN VALUES IN REALISTIC PADDED DATA")
print("="*80)

base_dir = Path(__file__).parent
data_file = base_dir / "solar_data_full_year_realistic_padded.csv"

print(f"\nLoading data from: {data_file.name}")
df = pd.read_csv(data_file)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')

# Check for NaN values
data_columns = ['cop_hsl_system_wide', 'stppf_system_wide', 'pvgrpp_system_wide']
print("\nNaN values before fix:")
for col in data_columns:
    nan_count = df[col].isna().sum()
    print(f"  {col}: {nan_count} NaN values")

# Add helper columns
df['month'] = df['interval_start_local'].dt.month
df['hour'] = df['interval_start_local'].dt.hour
df['day'] = df['interval_start_local'].dt.day

# For any remaining NaN values, use the monthly-hourly average
print("\nFilling remaining NaN values with monthly-hourly averages...")

for col in data_columns:
    if df[col].isna().any():
        # Calculate monthly-hourly averages from non-NaN data
        monthly_hourly_avg = df.groupby(['month', 'hour'])[col].mean()
        
        # Fill NaN values
        for idx in df[df[col].isna()].index:
            month = df.loc[idx, 'month']
            hour = df.loc[idx, 'hour']
            
            if (month, hour) in monthly_hourly_avg.index:
                avg_value = monthly_hourly_avg.loc[(month, hour)]
                if pd.notna(avg_value):
                    # Add small random variation
                    variation = np.random.uniform(-0.05, 0.05)
                    new_value = avg_value * (1 + variation)
                    new_value = max(0, new_value)  # Ensure non-negative
                    df.loc[idx, col] = new_value
                else:
                    # If monthly-hourly average is also NaN, use overall hourly average
                    overall_hourly_avg = df.groupby('hour')[col].mean()
                    if hour in overall_hourly_avg.index:
                        avg_value = overall_hourly_avg.loc[hour]
                        if pd.notna(avg_value):
                            df.loc[idx, col] = max(0, avg_value)
                        else:
                            df.loc[idx, col] = 0.0

# Check NaN values after fix
print("\nNaN values after fix:")
for col in data_columns:
    nan_count = df[col].isna().sum()
    print(f"  {col}: {nan_count} NaN values")

# If any columns still have NaN, fill with 0
for col in data_columns:
    if df[col].isna().any():
        print(f"  Filling remaining NaN in {col} with 0")
        df[col] = df[col].fillna(0)

# Drop temporary columns
df = df.drop(columns=['month', 'hour', 'day'], errors='ignore')

# Verify no NaN values remain
total_nan = df[data_columns].isna().sum().sum()
print(f"\nTotal NaN values remaining: {total_nan}")

if total_nan == 0:
    print("✓ All NaN values successfully filled!")
else:
    print("⚠ Warning: Some NaN values still remain")

# Save the fixed dataset
output_file = base_dir / "solar_data_full_year_realistic_padded.csv"
df.to_csv(output_file, index=False)
print(f"\n✓ Fixed data saved to: {output_file.name}")

# Verification statistics
print("\n" + "="*80)
print("VERIFICATION:")
print("="*80)
print(f"Total rows: {len(df)}")
print(f"Date range: {df['interval_start_local'].min()} to {df['interval_start_local'].max()}")
print(f"\nData statistics for cop_hsl_system_wide:")
print(f"  Mean: {df['cop_hsl_system_wide'].mean():,.2f} MW")
print(f"  Max: {df['cop_hsl_system_wide'].max():,.2f} MW")
print(f"  Min: {df['cop_hsl_system_wide'].min():,.2f} MW")
print(f"  Non-zero values: {(df['cop_hsl_system_wide'] > 0).sum()}")

print("\n" + "="*80)
print("FIX COMPLETE!")
print("="*80)
