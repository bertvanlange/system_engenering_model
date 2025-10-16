import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("IMPROVED PADDING - PRESERVING SEASONAL PATTERNS")
print("="*80)

# Load the combined data
base_dir = Path(__file__).parent
combined_file = base_dir / "solar_data_combined.csv"

print(f"\nLoading combined data from: {combined_file.name}")
df = pd.read_csv(combined_file)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df = df.sort_values('interval_start_local').reset_index(drop=True)

print(f"Original data: {len(df)} hours")

# Define the full year range
start_date = pd.Timestamp('2024-01-01 00:00:00', tz='US/Central')
end_date = pd.Timestamp('2024-12-31 23:00:00', tz='US/Central')

# Create full hourly range for the entire year
full_range = pd.date_range(start=start_date, end=end_date, freq='h')
print(f"Target hours: {len(full_range)}")

# Create a dataframe with all hours
padded_df = pd.DataFrame({'interval_start_local': full_range})
padded_df['month'] = padded_df['interval_start_local'].dt.month
padded_df['hour'] = padded_df['interval_start_local'].dt.hour

# Merge with existing data
padded_df = padded_df.merge(df, on='interval_start_local', how='left', suffixes=('', '_orig'))

# Get column names (excluding timestamp columns)
data_columns = [col for col in df.columns if col != 'interval_start_local' and 
                not col.endswith('_utc') and not col.startswith('interval_end') and 
                not col.startswith('publish_time')]

print(f"\nData columns to pad: {data_columns}")

print("\n" + "-"*80)
print("CALCULATING MONTH-SPECIFIC HOURLY PATTERNS")
print("-"*80)

# Add month and hour to original df for grouping
df['month'] = df['interval_start_local'].dt.month
df['hour'] = df['interval_start_local'].dt.hour

# Calculate average pattern for each month and hour combination
monthly_hourly_pattern = df.groupby(['month', 'hour'])[data_columns].mean().reset_index()

print("\nMonth-specific patterns calculated for:")
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for month in range(1, 13):
    month_data = monthly_hourly_pattern[monthly_hourly_pattern['month'] == month]
    if len(month_data) > 0:
        peak_hour_data = month_data[month_data['hour'].between(12, 14)]
        if len(peak_hour_data) > 0:
            avg_peak = peak_hour_data['cop_hsl_system_wide'].mean()
            print(f"  {month_names[month-1]}: Peak generation ~{avg_peak:,.0f} MW")

# Fill missing values using month-specific hourly patterns
print("\n" + "-"*80)
print("APPLYING MONTH-SPECIFIC PATTERNS TO MISSING DATA")
print("-"*80)

missing_mask = padded_df[data_columns[0]].isna()
missing_count = missing_mask.sum()
print(f"\nMissing hours to pad: {missing_count}")

# Merge with the monthly-hourly pattern
padded_df = padded_df.merge(
    monthly_hourly_pattern, 
    on=['month', 'hour'], 
    how='left', 
    suffixes=('', '_pattern')
)

# Fill missing values with the pattern values
for col in data_columns:
    pattern_col = f"{col}_pattern"
    if pattern_col in padded_df.columns:
        # Use pattern value only where original is NaN
        padded_df[col] = padded_df[col].fillna(padded_df[pattern_col])
        # Drop the pattern column
        padded_df.drop(columns=[pattern_col], inplace=True)

# Add back the timestamp columns with proper values
padded_df['interval_end_local'] = padded_df['interval_start_local'] + pd.Timedelta(hours=1)

# Convert to UTC
if 'interval_start_utc' in df.columns:
    padded_df['interval_start_utc'] = padded_df['interval_start_local'].dt.tz_convert('UTC')
    padded_df['interval_end_utc'] = padded_df['interval_end_local'].dt.tz_convert('UTC')

# Drop temporary columns
padded_df = padded_df.drop(columns=['month', 'hour'], errors='ignore')

print(f"\nPadded data: {len(padded_df)} hours")

# Check for any remaining missing values
missing_after = padded_df[data_columns].isna().sum().sum()
print(f"Remaining missing values: {missing_after}")

# Save the padded dataset
output_file = base_dir / "solar_data_full_year_seasonal_padded.csv"
padded_df.to_csv(output_file, index=False)
print(f"\n✓ Full year data with seasonal patterns saved to: {output_file.name}")

# Statistics comparison
print("\n" + "="*80)
print("SEASONAL VARIATION CHECK:")
print("="*80)

padded_df['month'] = padded_df['interval_start_local'].dt.month
monthly_avg = padded_df.groupby('month')['cop_hsl_system_wide'].mean()

print("\nAverage generation by month in padded data:")
for month in range(1, 13):
    avg = monthly_avg[month]
    print(f"  {month_names[month-1]:8s}: {avg:7.2f} MW")

summer_avg = monthly_avg[[6,7,8]].mean()
winter_avg = monthly_avg[[12,1,2]].mean()
print(f"\nSummer average: {summer_avg:,.2f} MW")
print(f"Winter average: {winter_avg:,.2f} MW")
print(f"Summer/Winter ratio: {summer_avg/winter_avg:.2f}x")

print("\n" + "="*80)
print("SEASONAL PADDING COMPLETE!")
print("="*80)
