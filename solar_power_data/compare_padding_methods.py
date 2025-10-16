import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

print("Creating seasonal comparison plot...")

base_dir = Path(__file__).parent

# Load both datasets
df_flat = pd.read_csv(base_dir / "solar_data_full_year_padded.csv")
df_seasonal = pd.read_csv(base_dir / "solar_data_full_year_seasonal_padded.csv")

df_flat['interval_start_local'] = pd.to_datetime(df_flat['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df_seasonal['interval_start_local'] = pd.to_datetime(df_seasonal['interval_start_local'], utc=True).dt.tz_convert('US/Central')

df_flat['month'] = df_flat['interval_start_local'].dt.month
df_seasonal['month'] = df_seasonal['interval_start_local'].dt.month

# Calculate monthly averages
monthly_flat = df_flat.groupby('month')['cop_hsl_system_wide'].mean()
monthly_seasonal = df_seasonal.groupby('month')['cop_hsl_system_wide'].mean()

# Create comparison plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# Plot 1: Flat padding (old method)
ax1.bar(range(1,13), monthly_flat.values, color='lightblue', alpha=0.7)
ax1.plot(range(1,13), monthly_flat.values, 'bo-', linewidth=2, markersize=8)
ax1.set_xticks(range(1,13))
ax1.set_xticklabels(months)
ax1.set_xlabel('Month', fontsize=12)
ax1.set_ylabel('Average Power (MW)', fontsize=12)
ax1.set_title('OLD METHOD: Flat Padding\n(All months look the same)', fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')
ax1.set_ylim(0, 7000)
for i, v in enumerate(monthly_flat.values, 1):
    ax1.text(i, v+150, f'{v:.0f}', ha='center', fontsize=9)

# Plot 2: Seasonal padding (new method)
ax2.bar(range(1,13), monthly_seasonal.values, color='orange', alpha=0.7)
ax2.plot(range(1,13), monthly_seasonal.values, 'ro-', linewidth=2, markersize=8)
ax2.set_xticks(range(1,13))
ax2.set_xticklabels(months)
ax2.set_xlabel('Month', fontsize=12)
ax2.set_ylabel('Average Power (MW)', fontsize=12)
ax2.set_title('NEW METHOD: Seasonal Padding\n(Summer 2x higher than Winter)', fontsize=13, fontweight='bold', color='darkgreen')
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_ylim(0, 7000)
for i, v in enumerate(monthly_seasonal.values, 1):
    ax2.text(i, v+150, f'{v:.0f}', ha='center', fontsize=9)

fig.suptitle('Comparison: Flat vs Seasonal Padding Methods', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout()

output_file = base_dir / "seasonal_vs_flat_comparison.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✓ Comparison plot saved to: {output_file.name}")

# Print statistics
print("\n" + "="*80)
print("COMPARISON STATISTICS:")
print("="*80)
print("\nFLAT PADDING (Old Method):")
print(f"  Summer avg: {monthly_flat[[6,7,8]].mean():.2f} MW")
print(f"  Winter avg: {monthly_flat[[12,1,2]].mean():.2f} MW")
print(f"  Ratio: {monthly_flat[[6,7,8]].mean() / monthly_flat[[12,1,2]].mean():.2f}x")

print("\nSEASONAL PADDING (New Method):")
print(f"  Summer avg: {monthly_seasonal[[6,7,8]].mean():.2f} MW")
print(f"  Winter avg: {monthly_seasonal[[12,1,2]].mean():.2f} MW")
print(f"  Ratio: {monthly_seasonal[[6,7,8]].mean() / monthly_seasonal[[12,1,2]].mean():.2f}x")

print("\n✓ Use 'solar_data_full_year_seasonal_padded.csv' for realistic seasonal data!")

plt.show()
