import pandas as pd
from pathlib import Path

print("="*80)
print("ANALYZING SEASONAL VARIATIONS IN ORIGINAL DATA")
print("="*80)

# Load combined original data (before padding)
base_dir = Path(__file__).parent
df = pd.read_csv(base_dir / "solar_data_combined.csv")
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df['month'] = df['interval_start_local'].dt.month
df['hour'] = df['interval_start_local'].dt.hour

solar_col = 'cop_hsl_system_wide'

print("\nOriginal data by month:")
print("-"*80)

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

for month in range(1, 13):
    month_data = df[df['month'] == month]
    if len(month_data) > 0:
        avg = month_data[solar_col].mean()
        peak = month_data[solar_col].max()
        print(f"{month_names[month-1]}: {len(month_data):4d} hours | Avg: {avg:7.2f} MW | Peak: {peak:7.2f} MW")
    else:
        print(f"{month_names[month-1]}: No data")

print("\n" + "-"*80)
print("COMPARING HOURLY PATTERNS BY SEASON")
print("-"*80)

# Group months by season
winter_months = [1, 2, 12]  # Jan, Feb, Dec
spring_months = [3, 4, 5]   # Mar, Apr, May
summer_months = [6, 7, 8]   # Jun, Jul, Aug
fall_months = [9, 10, 11]   # Sep, Oct, Nov

seasons = {
    'Winter': winter_months,
    'Spring': spring_months,
    'Summer': summer_months,
    'Fall': fall_months
}

print("\nPeak generation by season (hour 12-14):")
for season_name, months in seasons.items():
    season_data = df[(df['month'].isin(months)) & (df['hour'].between(12, 14))]
    if len(season_data) > 0:
        avg_peak = season_data[solar_col].mean()
        print(f"  {season_name:8s}: {avg_peak:7.2f} MW")
    else:
        print(f"  {season_name:8s}: No data")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("\nThe current padding uses a SINGLE average pattern for all months,")
print("which loses seasonal variations (winter vs summer solar patterns).")
print("\nTo preserve seasonal differences, we should:")
print("  1. Calculate separate patterns for each month")
print("  2. Use month-specific patterns when padding missing days")
print("="*80)
