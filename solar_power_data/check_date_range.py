import pandas as pd
from pathlib import Path

# Check date range in original file
file_path = Path(__file__).parent / "jan_2024_solar" / "900881b5-aa75-4e46-bcc9-dd73b18a57f6.csv"

print("="*80)
print("CHECKING DATE RANGE IN INTERVAL_START_LOCAL")
print("="*80)

df = pd.read_csv(file_path)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'])

# Get unique intervals
unique_intervals = df['interval_start_local'].unique()
unique_intervals = pd.to_datetime(unique_intervals)
unique_intervals = sorted(unique_intervals)

print(f"\nTotal unique intervals: {len(unique_intervals)}")
print(f"First interval: {unique_intervals[0]}")
print(f"Last interval: {unique_intervals[-1]}")
print(f"Expected days covered: {(unique_intervals[-1] - unique_intervals[0]).days + 1}")
print(f"Expected hours: {((unique_intervals[-1] - unique_intervals[0]).days + 1) * 24}")
print(f"Actual unique hours: {len(unique_intervals)}")

print("\n" + "-"*80)
print("FIRST 20 INTERVALS:")
print("-"*80)
for i, ts in enumerate(unique_intervals[:20]):
    print(f"{i+1}. {ts}")

print("\n" + "-"*80)
print("LAST 20 INTERVALS:")
print("-"*80)
for i, ts in enumerate(unique_intervals[-20:], start=len(unique_intervals)-19):
    print(f"{i}. {ts}")

# Check for gaps
print("\n" + "-"*80)
print("CHECKING FOR GAPS:")
print("-"*80)
gaps = []
for i in range(1, len(unique_intervals)):
    diff = (unique_intervals[i] - unique_intervals[i-1]).total_seconds() / 3600
    if diff > 1.1:  # Allow small tolerance
        gaps.append((unique_intervals[i-1], unique_intervals[i], diff))

if gaps:
    print(f"\nFound {len(gaps)} gap(s):")
    for start, end, hours in gaps:
        print(f"  Gap from {start} to {end}: {hours:.1f} hours")
else:
    print("\nNo gaps found - data is continuous!")
