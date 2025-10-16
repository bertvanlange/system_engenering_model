import pandas as pd
from pathlib import Path

# Analyze one original file
file_path = Path(__file__).parent / "jan_2024_solar" / "900881b5-aa75-4e46-bcc9-dd73b18a57f6.csv"

print("="*80)
print("ANALYZING ORIGINAL DATA FILE")
print("="*80)
print(f"\nFile: {file_path.name}\n")

df = pd.read_csv(file_path)

print(f"Total rows: {len(df)}")
print(f"\nColumns: {list(df.columns)}")
print("\n" + "-"*80)
print("SAMPLE DATA (first 10 rows):")
print("-"*80)
print(df.head(10).to_string())

print("\n" + "-"*80)
print("CHECKING FOR UNIQUE TIMESTAMPS:")
print("-"*80)

# Check each timestamp column
for col in ['interval_start_local', 'interval_end_local', 'interval_start_utc', 'interval_end_utc']:
    if col in df.columns:
        unique_count = df[col].nunique()
        print(f"{col}: {unique_count} unique values out of {len(df)} rows")

# Check if all timestamps are the same in interval_start_local
print("\n" + "-"*80)
print("CHECKING INTERVAL_START_LOCAL VALUES:")
print("-"*80)
df_temp = df.copy()
df_temp['interval_start_local'] = pd.to_datetime(df_temp['interval_start_local'])
print(f"Unique timestamps in interval_start_local: {df_temp['interval_start_local'].nunique()}")
print(f"\nValue counts (top 10):")
print(df_temp['interval_start_local'].value_counts().head(10))

# Check publish_time_local for the actual data timestamps
print("\n" + "-"*80)
print("CHECKING PUBLISH_TIME_LOCAL (might be the real timestamp):")
print("-"*80)
df_temp['publish_time_local'] = pd.to_datetime(df_temp['publish_time_local'])
print(f"Unique timestamps in publish_time_local: {df_temp['publish_time_local'].nunique()}")
print(f"Date range: {df_temp['publish_time_local'].min()} to {df_temp['publish_time_local'].max()}")
print(f"\nFirst 10 publish times:")
print(df_temp['publish_time_local'].head(10))
