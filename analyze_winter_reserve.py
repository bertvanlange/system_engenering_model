"""
Analyze the winter battery reserve feature.
Shows how battery SOC behaves during winter months (December & January).
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Load simulation results
results = pd.read_csv('output/simulation_results.csv', index_col=0)

# Create date column
start_date = datetime(2024, 1, 1)
results['date'] = [start_date + timedelta(hours=i) for i in range(len(results))]
results['month'] = results['date'].dt.month

# Filter for winter months (December and January)
winter_data = results[results['month'].isin([12, 1])].copy()
other_months = results[~results['month'].isin([12, 1])].copy()

# Create visualization
fig, axes = plt.subplots(3, 1, figsize=(14, 12))
fig.suptitle('Winter Battery Reserve Analysis (December & January)', 
             fontsize=16, fontweight='bold')

# Plot 1: Battery SOC throughout the year with winter highlighted
ax = axes[0]
ax.plot(results['date'], results['battery_soc'] * 100, 
        label='Battery SOC', color='green', linewidth=1.5)
ax.axhline(y=50, color='red', linestyle='--', linewidth=2, 
           label='Winter Reserve (50%)', alpha=0.7)

# Highlight winter months
for month in [1, 12]:
    month_data = results[results['month'] == month]
    if len(month_data) > 0:
        ax.fill_between(month_data['date'], 0, 100, 
                        alpha=0.2, color='lightblue', label='Winter Period' if month == 1 else '')

ax.set_ylabel('Battery SOC (%)', fontsize=12)
ax.set_title('Battery State of Charge - Full Year', fontsize=13, fontweight='bold')
ax.set_ylim([0, 100])
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.xaxis.set_major_locator(mdates.MonthLocator())

# Plot 2: Detailed winter SOC
ax = axes[1]
if len(winter_data) > 0:
    ax.plot(winter_data['date'], winter_data['battery_soc'] * 100, 
            label='Battery SOC (Winter)', color='blue', linewidth=2)
    ax.axhline(y=50, color='red', linestyle='--', linewidth=2, 
               label='Minimum Reserve (50%)', alpha=0.7)
    ax.fill_between(winter_data['date'], 50, winter_data['battery_soc'] * 100, 
                    where=(winter_data['battery_soc'] * 100 >= 50), 
                    alpha=0.3, color='green', label='Above Reserve')
    ax.fill_between(winter_data['date'], 0, 50, 
                    alpha=0.2, color='red', label='Reserve Zone')
    
ax.set_ylabel('Battery SOC (%)', fontsize=12)
ax.set_title('Battery SOC During Winter Months (Dec & Jan)', fontsize=13, fontweight='bold')
ax.set_ylim([0, 100])
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))

# Plot 3: Grid dependency comparison
ax = axes[2]
winter_grid_import = winter_data.groupby('month')['grid_import'].sum()
other_grid_import = other_months.groupby('month')['grid_import'].sum()

all_months = pd.DataFrame({
    'month': range(1, 13),
    'grid_import': [winter_grid_import.get(m, other_grid_import.get(m, 0)) for m in range(1, 13)]
})

colors = ['red' if m in [1, 12] else 'blue' for m in all_months['month']]
bars = ax.bar(all_months['month'], all_months['grid_import'], color=colors, alpha=0.7)

# Add legend
from matplotlib.patches import Patch
legend_elements = [Patch(facecolor='red', alpha=0.7, label='Winter Months (Reserve Active)'),
                   Patch(facecolor='blue', alpha=0.7, label='Other Months')]
ax.legend(handles=legend_elements, loc='upper right')

ax.set_xlabel('Month', fontsize=12)
ax.set_ylabel('Grid Import (kWh)', fontsize=12)
ax.set_title('Grid Import by Month (Shows Winter Reserve Impact)', fontsize=13, fontweight='bold')
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('output/winter_reserve_analysis.png', dpi=150, bbox_inches='tight')
print("Winter reserve analysis saved to: output/winter_reserve_analysis.png")

# Print statistics
print("\n" + "=" * 60)
print("Winter Reserve Statistics")
print("=" * 60)

print(f"\nWinter Months (Dec & Jan):")
print(f"  Average SOC: {winter_data['battery_soc'].mean() * 100:.2f}%")
print(f"  Minimum SOC: {winter_data['battery_soc'].min() * 100:.2f}%")
print(f"  Grid import: {winter_data['grid_import'].sum():.2f} kWh")
print(f"  Times below 50% SOC: {(winter_data['battery_soc'] < 0.5).sum()} hours")

print(f"\nOther Months:")
print(f"  Average SOC: {other_months['battery_soc'].mean() * 100:.2f}%")
print(f"  Minimum SOC: {other_months['battery_soc'].min() * 100:.2f}%")
print(f"  Grid import: {other_months['grid_import'].sum():.2f} kWh")

print(f"\nWinter Reserve Impact:")
winter_import_pct = (winter_data['grid_import'].sum() / results['grid_import'].sum()) * 100
print(f"  Winter months account for {winter_import_pct:.1f}% of total grid import")
print(f"  Reserve ensures battery stays charged for outages during low solar months")

plt.show()
