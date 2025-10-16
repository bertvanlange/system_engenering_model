import pandas as pd
import numpy as np
from pathlib import Path

print("="*80)
print("IMPROVED PADDING - WITH DAY-TO-DAY VARIATION")
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
padded_df['day'] = padded_df['interval_start_local'].dt.day
padded_df['hour'] = padded_df['interval_start_local'].dt.hour

# Merge with existing data
padded_df = padded_df.merge(df, on='interval_start_local', how='left')

# Get column names (excluding timestamp columns)
data_columns = [col for col in df.columns if col != 'interval_start_local' and 
                not col.endswith('_utc') and not col.startswith('interval_end') and 
                not col.startswith('publish_time')]

print(f"\nData columns to pad: {data_columns}")

print("\n" + "-"*80)
print("PADDING STRATEGY:")
print("-"*80)
print("For each missing day in a month:")
print("  1. Find all available days in the same month")
print("  2. Randomly select one of those days as a template")
print("  3. Add small random variations (+/- 5%) to simulate weather differences")
print("  4. This creates realistic day-to-day variation")
print("-"*80)

# Add month and day to original df for grouping
df['month'] = df['interval_start_local'].dt.month
df['day'] = df['interval_start_local'].dt.day
df['hour'] = df['interval_start_local'].dt.hour

# Identify missing data
missing_mask = padded_df[data_columns[0]].isna()
missing_count = missing_mask.sum()
print(f"\nMissing hours to pad: {missing_count}")

# Set random seed for reproducibility
np.random.seed(42)

# Process each month
print("\nPadding by month:")
for month in range(1, 13):
    month_data = padded_df[padded_df['month'] == month]
    
    # Get available days in this month from original data
    available_days = df[df['month'] == month]['day'].unique()
    
    if len(available_days) == 0:
        print(f"  Month {month:2d}: No original data available, skipping")
        continue
    
    # Get missing days in this month
    all_days_in_month = month_data['day'].unique()
    missing_days = [d for d in all_days_in_month if d not in available_days]
    
    if len(missing_days) == 0:
        print(f"  Month {month:2d}: No missing days")
        continue
    
    print(f"  Month {month:2d}: Padding {len(missing_days)} days using {len(available_days)} available days")
    
    # For each missing day
    for missing_day in missing_days:
        # Randomly select a template day from available days
        template_day = np.random.choice(available_days)
        
        # Get the template day's data
        template_data = df[(df['month'] == month) & (df['day'] == template_day)].copy()
        
        if len(template_data) == 0:
            continue
        
        # For each hour of the missing day
        for hour in range(24):
            # Find the corresponding hour in the template
            template_hour_data = template_data[template_data['hour'] == hour]
            
            if len(template_hour_data) == 0:
                continue
            
            # Get the index for this missing hour
            missing_idx = padded_df[
                (padded_df['month'] == month) & 
                (padded_df['day'] == missing_day) & 
                (padded_df['hour'] == hour)
            ].index
            
            if len(missing_idx) == 0:
                continue
            
            # Copy the template values with small random variations
            for col in data_columns:
                if col in template_hour_data.columns:
                    base_value = template_hour_data[col].iloc[0]
                    
                    if pd.notna(base_value) and base_value > 0:
                        # Add random variation: +/- 5%
                        variation = np.random.uniform(-0.05, 0.05)
                        new_value = base_value * (1 + variation)
                        # Ensure non-negative
                        new_value = max(0, new_value)
                        padded_df.loc[missing_idx[0], col] = new_value
                    else:
                        padded_df.loc[missing_idx[0], col] = base_value

# Add back the timestamp columns
padded_df['interval_end_local'] = padded_df['interval_start_local'] + pd.Timedelta(hours=1)

# Convert to UTC
if 'interval_start_utc' in df.columns:
    padded_df['interval_start_utc'] = padded_df['interval_start_local'].dt.tz_convert('UTC')
    padded_df['interval_end_utc'] = padded_df['interval_end_local'].dt.tz_convert('UTC')

# Drop temporary columns
padded_df = padded_df.drop(columns=['month', 'day', 'hour'], errors='ignore')

print(f"\nPadded data: {len(padded_df)} hours")

# Check for any remaining missing values
missing_after = padded_df[data_columns].isna().sum().sum()
print(f"Remaining missing values: {missing_after}")

# Save the padded dataset
output_file = base_dir / "solar_data_full_year_realistic_padded.csv"
padded_df.to_csv(output_file, index=False)
print(f"\n✓ Realistic padded data saved to: {output_file.name}")

# Verification - check variation within a month
print("\n" + "="*80)
print("VERIFYING DAY-TO-DAY VARIATION:")
print("="*80)

padded_df['month'] = padded_df['interval_start_local'].dt.month
padded_df['day'] = padded_df['interval_start_local'].dt.day

# Check June as an example
june_data = padded_df[padded_df['month'] == 6]
june_daily = june_data.groupby('day')['cop_hsl_system_wide'].sum()

print("\nJune daily totals (MWh) - showing variation:")
for day in range(1, min(21, len(june_daily)+1)):
    if day in june_daily.index:
        marker = "← Original" if day <= 10 else "← Padded"
        print(f"  Day {day:2d}: {june_daily[day]:8,.0f} MWh {marker}")

# Calculate coefficient of variation
june_cv = june_daily.std() / june_daily.mean() * 100
print(f"\nCoefficient of Variation: {june_cv:.2f}%")
print("(Higher % = more day-to-day variation, which is realistic)")

# Monthly averages
print("\n" + "-"*80)
print("Monthly averages (should show seasonal pattern):")
print("-"*80)
monthly_avg = padded_df.groupby('month')['cop_hsl_system_wide'].mean()
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for month in range(1, 13):
    print(f"  {month_names[month-1]:8s}: {monthly_avg[month]:7,.0f} MW")

print("\n" + "="*80)
print("REALISTIC PADDING COMPLETE!")
print("="*80)
print("\nThis dataset now has:")
print("  ✓ Seasonal variations (summer vs winter)")
print("  ✓ Day-to-day variations within each month")
print("  ✓ Random weather-like fluctuations")
