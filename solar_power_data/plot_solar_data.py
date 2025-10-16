import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import numpy as np

print("="*80)
print("PLOTTING SOLAR DATA")
print("="*80)

# Load the realistic padded data (with day-to-day variation)
base_dir = Path(__file__).parent
data_file = base_dir / "solar_data_full_year_realistic_padded.csv"

print(f"\nLoading data from: {data_file.name}")
df = pd.read_csv(data_file)
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df['date'] = df['interval_start_local'].dt.date
df['hour'] = df['interval_start_local'].dt.hour
df['month'] = df['interval_start_local'].dt.month

print(f"Loaded {len(df)} hours of data")
print(f"Date range: {df['interval_start_local'].min()} to {df['interval_start_local'].max()}")

# Create figure with multiple subplots
fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Use the main solar generation column
solar_col = 'cop_hsl_system_wide'

# 1. Full Year Time Series
print("\nCreating Plot 1: Full Year Time Series...")
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(df['interval_start_local'], df[solar_col], linewidth=0.5, color='orange', alpha=0.7)
ax1.set_title('Solar Power Generation - Full Year 2024', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Power Output (MW)', fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# Add shading to show original vs padded data
original_end = pd.Timestamp('2024-01-13 23:00:00', tz='US/Central')
ax1.axvspan(df['interval_start_local'].min(), original_end, alpha=0.1, color='green', label='Original Data Period (Jan 1-13)')
ax1.legend(loc='upper right')

# 2. Sample Week (first week of June)
print("Creating Plot 2: Sample Week Detail...")
ax2 = fig.add_subplot(gs[1, 0])
june_week = df[(df['interval_start_local'] >= '2024-06-01') & (df['interval_start_local'] <= '2024-06-07')]
ax2.plot(june_week['interval_start_local'], june_week[solar_col], linewidth=1.5, color='darkorange')
ax2.set_title('Solar Generation - Sample Week (June 1-7)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Date', fontsize=10)
ax2.set_ylabel('Power Output (MW)', fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax2.fill_between(june_week['interval_start_local'], june_week[solar_col], alpha=0.3, color='orange')

# 3. Average Daily Pattern
print("Creating Plot 3: Average Daily Pattern...")
ax3 = fig.add_subplot(gs[1, 1])
hourly_avg = df.groupby('hour')[solar_col].mean()
ax3.plot(hourly_avg.index, hourly_avg.values, linewidth=2.5, color='red', marker='o', markersize=5)
ax3.set_title('Average Daily Solar Pattern', fontsize=12, fontweight='bold')
ax3.set_xlabel('Hour of Day', fontsize=10)
ax3.set_ylabel('Average Power Output (MW)', fontsize=10)
ax3.grid(True, alpha=0.3)
ax3.set_xticks(range(0, 24, 2))
ax3.fill_between(hourly_avg.index, hourly_avg.values, alpha=0.3, color='red')

# 4. Monthly Average Generation
print("Creating Plot 4: Monthly Statistics...")
ax4 = fig.add_subplot(gs[2, 0])
monthly_stats = df.groupby('month')[solar_col].agg(['mean', 'max'])
months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
ax4.bar(monthly_stats.index, monthly_stats['mean'], color='orange', alpha=0.7, label='Average')
ax4.plot(monthly_stats.index, monthly_stats['max'], color='red', marker='o', linewidth=2, label='Peak')
ax4.set_title('Monthly Solar Generation Statistics', fontsize=12, fontweight='bold')
ax4.set_xlabel('Month', fontsize=10)
ax4.set_ylabel('Power Output (MW)', fontsize=10)
ax4.set_xticks(range(1, 13))
ax4.set_xticklabels(months)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

# 5. Heatmap - Hour vs Month
print("Creating Plot 5: Generation Heatmap...")
ax5 = fig.add_subplot(gs[2, 1])
pivot_data = df.groupby(['month', 'hour'])[solar_col].mean().reset_index()
heatmap_data = pivot_data.pivot(index='hour', columns='month', values=solar_col)
im = ax5.imshow(heatmap_data, aspect='auto', cmap='YlOrRd', origin='lower')
ax5.set_title('Solar Generation Heatmap (Hour vs Month)', fontsize=12, fontweight='bold')
ax5.set_xlabel('Month', fontsize=10)
ax5.set_ylabel('Hour of Day', fontsize=10)
ax5.set_xticks(range(12))
ax5.set_xticklabels(months)
ax5.set_yticks(range(0, 24, 3))
plt.colorbar(im, ax=ax5, label='Power Output (MW)')

# Add main title
fig.suptitle('Solar Power Data Analysis - 2024 (Realistic Padded - with Daily Variations)', 
             fontsize=16, fontweight='bold', y=0.995)

# Save the plot
output_file = base_dir / "solar_data_visualization.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✓ Plot saved to: {output_file.name}")

# Create additional single-day plot for detail
print("\nCreating detailed single-day plot...")
fig2, ax = plt.subplots(figsize=(12, 6))
single_day = df[df['date'] == pd.Timestamp('2024-06-15').date()]
ax.plot(single_day['hour'], single_day[solar_col], linewidth=3, color='darkorange', marker='o', markersize=8)
ax.fill_between(single_day['hour'], single_day[solar_col], alpha=0.3, color='orange')
ax.set_title('Solar Generation - Single Day Example (June 15, 2024)', fontsize=14, fontweight='bold')
ax.set_xlabel('Hour of Day', fontsize=12)
ax.set_ylabel('Power Output (MW)', fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xticks(range(0, 24))
ax.set_xlim(-0.5, 23.5)

# Add sunrise/sunset annotations
sunrise_hour = 6
sunset_hour = 20
ax.axvline(sunrise_hour, color='yellow', linestyle='--', alpha=0.5, linewidth=2, label='~Sunrise')
ax.axvline(sunset_hour, color='purple', linestyle='--', alpha=0.5, linewidth=2, label='~Sunset')
ax.legend()

output_file2 = base_dir / "solar_data_single_day.png"
plt.savefig(output_file2, dpi=300, bbox_inches='tight')
print(f"✓ Single day plot saved to: {output_file2.name}")

# Print statistics
print("\n" + "="*80)
print("DATA STATISTICS:")
print("="*80)
print(f"Total energy generated (sum): {df[solar_col].sum():,.0f} MWh")
print(f"Average hourly generation: {df[solar_col].mean():,.2f} MW")
print(f"Peak generation: {df[solar_col].max():,.2f} MW")
print(f"Minimum generation: {df[solar_col].min():,.2f} MW")
print(f"Standard deviation: {df[solar_col].std():,.2f} MW")

# Calculate daily totals
daily_totals = df.groupby('date')[solar_col].sum()
print(f"\nAverage daily total: {daily_totals.mean():,.2f} MWh/day")
print(f"Best day: {daily_totals.idxmax()} with {daily_totals.max():,.2f} MWh")
print(f"Lowest day: {daily_totals.idxmin()} with {daily_totals.min():,.2f} MWh")

print("\n" + "="*80)
print("PLOTTING COMPLETE!")
print("="*80)
print("\nGenerated files:")
print(f"  1. {output_file.name} - Comprehensive multi-panel visualization")
print(f"  2. {output_file2.name} - Detailed single-day view")

plt.show()
