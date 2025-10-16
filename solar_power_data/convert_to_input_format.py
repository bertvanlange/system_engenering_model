import pandas as pd
from pathlib import Path

print("="*80)
print("CONVERTING SOLAR DATA TO INPUT_DATA FORMAT")
print("="*80)

# Load the realistic padded solar data
base_dir = Path(__file__).parent
data_file = base_dir / "solar_data_full_year_realistic_padded.csv"

print(f"\nLoading data from: {data_file.name}")
df = pd.read_csv(data_file)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')

# Extract hour from timestamp
df['hour'] = df['interval_start_local'].dt.hour

# Use the main solar generation column (MW)
solar_col = 'cop_hsl_system_wide'

print(f"Total rows: {len(df)}")
print(f"Date range: {df['interval_start_local'].min()} to {df['interval_start_local'].max()}")

# Create output dataframe with just hour and generation values
# Format: hour, solar_generation_mw (all 8784 hours)
output_df = pd.DataFrame({
    'hour': range(len(df)),
    'solar_generation_mw': df[solar_col].values
})

# Save to input_data folder
output_dir = base_dir.parent / "input_data"
output_file = output_dir / "solar_irradiation.csv"

# Check if output directory exists
if not output_dir.exists():
    print(f"\nCreating directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

output_df.to_csv(output_file, index=False)
print(f"\n✓ Saved to: {output_file}")

# Display statistics
print("\n" + "="*80)
print("OUTPUT FILE STATISTICS:")
print("="*80)
print(f"Total hours: {len(output_df)}")
print(f"Column name: solar_generation_mw")
print(f"Mean generation: {output_df['solar_generation_mw'].mean():,.2f} MW")
print(f"Max generation: {output_df['solar_generation_mw'].max():,.2f} MW")
print(f"Min generation: {output_df['solar_generation_mw'].min():,.2f} MW")

print("\nFirst 10 rows:")
print(output_df.head(10).to_string(index=False))

print("\nLast 10 rows:")
print(output_df.tail(10).to_string(index=False))

# Also create a version with just values (no header)
output_file_values_only = output_dir / "solar_irradiation_values_only.csv"
df[solar_col].to_csv(output_file_values_only, index=False, header=False)
print(f"\n✓ Also saved values-only version to: {output_file_values_only.name}")

print("\n" + "="*80)
print("CONVERSION COMPLETE!")
print("="*80)
print("\nCreated files in input_data/:")
print(f"  1. solar_irradiation.csv - with 'hour' and 'solar_generation_mw' columns")
print(f"  2. solar_irradiation_values_only.csv - single column, values only")
print("\nNote: The original solar_irradiation.csv has been backed up if it existed.")
