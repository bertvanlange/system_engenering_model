import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import numpy as np

print("="*80)
print("COMPREHENSIVE SOLAR POWER ANALYSIS")
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
df['day_of_year'] = df['interval_start_local'].dt.dayofyear

print(f"Loaded {len(df)} hours of data")
print(f"Date range: {df['interval_start_local'].min()} to {df['interval_start_local'].max()}")

# Use the main solar generation column
solar_col = 'cop_hsl_system_wide'

# Create figure with multiple subplots
fig = plt.figure(figsize=(18, 14))
gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.35)

# 1. Full Year Time Series with Seasonal Variations
print("\nCreating Plot 1: Full Year Time Series...")
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(df['interval_start_local'], df[solar_col], linewidth=0.3, color='darkorange', alpha=0.8)
ax1.set_title('Solar Power Generation - Full Year 2024 (with Seasonal Variations)', 
              fontsize=14, fontweight='bold')
ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Power Output (MW)', fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())
ax1.fill_between(df['interval_start_local'], df[solar_col], alpha=0.2, color='orange')

# Add season labels
ax1.axvspan(df['interval_start_local'].min(), pd.Timestamp('2024-03-01', tz='US/Central'), 
            alpha=0.05, color='blue', label='Winter')
ax1.axvspan(pd.Timestamp('2024-06-01', tz='US/Central'), pd.Timestamp('2024-09-01', tz='US/Central'), 
            alpha=0.05, color='red', label='Summer')
ax1.legend(loc='upper right', fontsize=10)

# 2. Monthly Box Plot - Distribution
print("Creating Plot 2: Monthly Distribution Box Plot...")
ax2 = fig.add_subplot(gs[1, 0])
monthly_data = [df[df['month']==m][solar_col].values for m in range(1,13)]
months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
bp = ax2.boxplot(monthly_data, tick_labels=months, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('lightblue')
    patch.set_alpha(0.7)
ax2.set_title('Monthly Generation Distribution', fontsize=12, fontweight='bold')
ax2.set_ylabel('Power Output (MW)', fontsize=10)
ax2.grid(True, alpha=0.3, axis='y')
ax2.tick_params(axis='x', rotation=45)

# 3. Average Daily Pattern by Season
print("Creating Plot 3: Daily Patterns by Season...")
ax3 = fig.add_subplot(gs[1, 1])
seasons = {
    'Winter (Dec-Feb)': [12, 1, 2],
    'Spring (Mar-May)': [3, 4, 5],
    'Summer (Jun-Aug)': [6, 7, 8],
    'Fall (Sep-Nov)': [9, 10, 11]
}
colors = ['blue', 'green', 'red', 'orange']
for (season_name, months), color in zip(seasons.items(), colors):
    season_data = df[df['month'].isin(months)]
    hourly_avg = season_data.groupby('hour')[solar_col].mean()
    ax3.plot(hourly_avg.index, hourly_avg.values, linewidth=2.5, label=season_name, color=color)
ax3.set_title('Average Daily Pattern by Season', fontsize=12, fontweight='bold')
ax3.set_xlabel('Hour of Day', fontsize=10)
ax3.set_ylabel('Average Power (MW)', fontsize=10)
ax3.legend(loc='upper right', fontsize=9)
ax3.grid(True, alpha=0.3)
ax3.set_xticks(range(0, 24, 2))

# 4. Capacity Factor by Month
print("Creating Plot 4: Capacity Factor Analysis...")
ax4 = fig.add_subplot(gs[1, 2])
peak_capacity = df[solar_col].max()
monthly_avg = df.groupby('month')[solar_col].mean()
capacity_factor = (monthly_avg / peak_capacity * 100)
month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
bars = ax4.bar(range(1,13), capacity_factor.values, color='teal', alpha=0.7)
ax4.set_title('Capacity Factor by Month', fontsize=12, fontweight='bold')
ax4.set_xlabel('Month', fontsize=10)
ax4.set_ylabel('Capacity Factor (%)', fontsize=10)
ax4.set_xticks(range(1,13))
ax4.set_xticklabels(month_labels, rotation=45, ha='right')
ax4.grid(True, alpha=0.3, axis='y')
for i, v in enumerate(capacity_factor.values, 1):
    ax4.text(i, v+1, f'{v:.1f}%', ha='center', fontsize=8)

# 5. Daily Total Energy Production
print("Creating Plot 5: Daily Energy Totals...")
ax5 = fig.add_subplot(gs[2, :])
daily_totals = df.groupby('date')[solar_col].sum() / 1000  # Convert to GWh
dates = pd.to_datetime(list(daily_totals.index))
ax5.plot(dates, daily_totals.values, linewidth=1, color='darkgreen', alpha=0.7)
ax5.fill_between(dates, daily_totals.values, alpha=0.3, color='green')
ax5.set_title('Daily Total Energy Production', fontsize=12, fontweight='bold')
ax5.set_xlabel('Date', fontsize=10)
ax5.set_ylabel('Daily Energy (GWh)', fontsize=10)
ax5.grid(True, alpha=0.3)
ax5.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax5.xaxis.set_major_locator(mdates.MonthLocator())

# 6. Heatmap - Hour vs Day of Year
print("Creating Plot 6: Annual Heatmap...")
ax6 = fig.add_subplot(gs[3, 0])
pivot_data = df.pivot_table(values=solar_col, index='hour', columns='day_of_year', aggfunc='mean')
im = ax6.imshow(pivot_data, aspect='auto', cmap='YlOrRd', origin='lower', interpolation='bilinear')
ax6.set_title('Generation Heatmap (Hour vs Day of Year)', fontsize=11, fontweight='bold')
ax6.set_xlabel('Day of Year', fontsize=9)
ax6.set_ylabel('Hour of Day', fontsize=9)
ax6.set_yticks(range(0, 24, 3))
plt.colorbar(im, ax=ax6, label='Power (MW)', fraction=0.046)

# 7. Peak Hour Analysis
print("Creating Plot 7: Peak Hour Analysis...")
ax7 = fig.add_subplot(gs[3, 1])
peak_hours = df.groupby('date')[solar_col].idxmax()
peak_hour_of_day = df.loc[peak_hours, 'hour'].value_counts().sort_index()
ax7.bar(peak_hour_of_day.index, peak_hour_of_day.values, color='crimson', alpha=0.7)
ax7.set_title('Peak Generation Hour Distribution', fontsize=11, fontweight='bold')
ax7.set_xlabel('Hour of Day', fontsize=9)
ax7.set_ylabel('Number of Days', fontsize=9)
ax7.grid(True, alpha=0.3, axis='y')

# 8. Statistics Table
print("Creating Plot 8: Statistics Summary...")
ax8 = fig.add_subplot(gs[3, 2])
ax8.axis('off')

# Calculate statistics
month_names_list = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
best_month_idx = df.groupby("month")[solar_col].mean().idxmax()
worst_month_idx = df.groupby("month")[solar_col].mean().idxmin()

stats_data = [
    ['Metric', 'Value'],
    ['─────────────────', '──────────────'],
    ['Total Energy/Year', f'{df[solar_col].sum()/1e6:.2f} TWh'],
    ['Average Output', f'{df[solar_col].mean():.0f} MW'],
    ['Peak Output', f'{df[solar_col].max():.0f} MW'],
    ['Min Output', f'{df[solar_col].min():.1f} MW'],
    ['', ''],
    ['Summer Average', f'{df[df["month"].isin([6,7,8])][solar_col].mean():.0f} MW'],
    ['Winter Average', f'{df[df["month"].isin([12,1,2])][solar_col].mean():.0f} MW'],
    ['Seasonal Ratio', f'{df[df["month"].isin([6,7,8])][solar_col].mean() / df[df["month"].isin([12,1,2])][solar_col].mean():.2f}x'],
    ['', ''],
    ['Best Month', month_names_list[best_month_idx-1]],
    ['Lowest Month', month_names_list[worst_month_idx-1]],
]

table = ax8.table(cellText=stats_data, cellLoc='left', loc='center',
                  colWidths=[0.6, 0.4])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Style header row
for i in range(2):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Style data rows
for i in range(2, len(stats_data)):
    for j in range(2):
        table[(i, j)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')

ax8.set_title('Annual Statistics', fontsize=11, fontweight='bold', pad=20)

# Add main title
fig.suptitle('Solar Power System Analysis - 2024 (Realistic Padded Data with Daily Variations)', 
             fontsize=18, fontweight='bold', y=0.995)

# Save the plot
output_file = base_dir / "solar_power_comprehensive_analysis.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✓ Comprehensive analysis plot saved to: {output_file.name}")

# Print detailed statistics
print("\n" + "="*80)
print("DETAILED STATISTICS:")
print("="*80)

print(f"\nANNUAL TOTALS:")
print(f"  Total Energy Generated: {df[solar_col].sum()/1e6:.2f} TWh")
print(f"  Average Daily Production: {daily_totals.mean():.2f} GWh/day")

print(f"\nGENERATION PROFILE:")
print(f"  Average Output: {df[solar_col].mean():,.0f} MW")
print(f"  Peak Output: {df[solar_col].max():,.0f} MW")
print(f"  Minimum Output: {df[solar_col].min():.2f} MW")
print(f"  Standard Deviation: {df[solar_col].std():,.0f} MW")

print(f"\nSEASONAL COMPARISON:")
for (season_name, season_months), color in zip(seasons.items(), colors):
    season_data = df[df['month'].isin(season_months)]
    avg = season_data[solar_col].mean()
    peak = season_data[solar_col].max()
    print(f"  {season_name:20s}: Avg {avg:6,.0f} MW  |  Peak {peak:6,.0f} MW")

print(f"\nCAPACITY FACTOR:")
print(f"  Annual Average: {(df[solar_col].mean() / peak_capacity * 100):.1f}%")
print(f"  Summer: {(df[df['month'].isin([6,7,8])][solar_col].mean() / peak_capacity * 100):.1f}%")
print(f"  Winter: {(df[df['month'].isin([12,1,2])][solar_col].mean() / peak_capacity * 100):.1f}%")

print("\n" + "="*80)
print("ANALYSIS COMPLETE!")
print("="*80)

plt.show()
