"""
Compare different outage scenarios and demonstrate the value of winter battery reserve.
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load different outage files
outage_files = {
    'Random Texas': 'input_data/grid_stability_random_texas.csv',
    'Seasonal Moderate': 'input_data/grid_stability_seasonal_moderate.csv',
    'Seasonal Severe': 'input_data/grid_stability_seasonal_severe.csv'
}

fig, axes = plt.subplots(4, 1, figsize=(15, 12))
fig.suptitle('Power Outage Scenario Comparison', fontsize=16, fontweight='bold')

for scenario_name, file_path in outage_files.items():
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        
        # Create month column (assuming starts Jan 1)
        df['month'] = (df['hour'] // 730) + 1
        df['month'] = df['month'].clip(1, 12)
        
        # Calculate outages (grid_stable == False)
        df['outage'] = ~df['grid_stable']
        
        # Monthly outage statistics
        monthly_stats = df.groupby('month').agg({
            'outage': ['sum', 'count']
        }).reset_index()
        monthly_stats.columns = ['month', 'outage_hours', 'total_hours']
        monthly_stats['outage_pct'] = (monthly_stats['outage_hours'] / monthly_stats['total_hours']) * 100
        
        # Plot 1: Monthly outage percentage
        ax = axes[0]
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.plot(monthly_stats['month'], monthly_stats['outage_pct'], 
               marker='o', linewidth=2, label=scenario_name)
        ax.set_ylabel('Outage %', fontsize=11)
        ax.set_title('Monthly Outage Percentage by Scenario', fontsize=12, fontweight='bold')
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(month_labels)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Highlight winter months
        winter_months = [1, 2, 12]
        for month in winter_months:
            ax.axvspan(month - 0.4, month + 0.4, alpha=0.1, color='lightblue')

# Plot 2: Total outage hours by scenario
ax = axes[1]
scenario_totals = []
scenario_names = []
winter_totals = []

for scenario_name, file_path in outage_files.items():
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        df['month'] = (df['hour'] // 730) + 1
        df['month'] = df['month'].clip(1, 12)
        df['outage'] = ~df['grid_stable']
        
        total_outage = df['outage'].sum()
        winter_outage = df[df['month'].isin([1, 2, 12])]['outage'].sum()
        
        scenario_names.append(scenario_name)
        scenario_totals.append(total_outage)
        winter_totals.append(winter_outage)

x = np.arange(len(scenario_names))
width = 0.35

bars1 = ax.bar(x - width/2, scenario_totals, width, label='Total Outage Hours', color='orange')
bars2 = ax.bar(x + width/2, winter_totals, width, label='Winter Outage Hours', color='red')

ax.set_ylabel('Hours', fontsize=11)
ax.set_title('Total Outage Hours Comparison', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(scenario_names)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=9)

# Plot 3: Outage duration distribution
ax = axes[2]
for scenario_name, file_path in outage_files.items():
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        df['outage'] = ~df['grid_stable']
        
        # Find continuous outage periods
        outage_periods = []
        in_outage = False
        current_duration = 0
        
        for idx, row in df.iterrows():
            if row['outage']:
                if not in_outage:
                    in_outage = True
                    current_duration = 1
                else:
                    current_duration += 1
            else:
                if in_outage:
                    outage_periods.append(current_duration)
                    in_outage = False
                    current_duration = 0
        
        if in_outage:
            outage_periods.append(current_duration)
        
        # Plot histogram
        if outage_periods:
            bins = [0, 6, 12, 24, 48, 72, 96, 120, max(outage_periods)+1]
            ax.hist(outage_periods, bins=bins, alpha=0.5, label=scenario_name, edgecolor='black')

ax.set_xlabel('Outage Duration (hours)', fontsize=11)
ax.set_ylabel('Number of Outages', fontsize=11)
ax.set_title('Outage Duration Distribution', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.set_xlim(0, 120)

# Plot 4: Summary statistics table
ax = axes[3]
ax.axis('off')

table_data = []
table_data.append(['Scenario', 'Total\nOutages', 'Winter\nOutages', 'Longest\nOutage', 'Avg\nOutage', 'Winter\n% of Year'])

for scenario_name, file_path in outage_files.items():
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        df['month'] = (df['hour'] // 730) + 1
        df['month'] = df['month'].clip(1, 12)
        df['outage'] = ~df['grid_stable']
        
        total_outage = df['outage'].sum()
        winter_outage = df[df['month'].isin([1, 2, 12])]['outage'].sum()
        winter_pct = (winter_outage / total_outage * 100) if total_outage > 0 else 0
        
        # Find outage periods
        outage_periods = []
        in_outage = False
        current_duration = 0
        
        for idx, row in df.iterrows():
            if row['outage']:
                if not in_outage:
                    in_outage = True
                    current_duration = 1
                else:
                    current_duration += 1
            else:
                if in_outage:
                    outage_periods.append(current_duration)
                    in_outage = False
                    current_duration = 0
        
        if in_outage:
            outage_periods.append(current_duration)
        
        longest = max(outage_periods) if outage_periods else 0
        avg = np.mean(outage_periods) if outage_periods else 0
        
        table_data.append([
            scenario_name,
            f'{total_outage}h',
            f'{winter_outage}h',
            f'{longest}h',
            f'{avg:.1f}h',
            f'{winter_pct:.0f}%'
        ])

table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                colWidths=[0.25, 0.15, 0.15, 0.15, 0.15, 0.15])
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2)

# Style header row
for i in range(6):
    table[(0, i)].set_facecolor('#4CAF50')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Color winter-heavy scenarios
for i in range(1, len(table_data)):
    winter_pct = float(table_data[i][5].rstrip('%'))
    if winter_pct > 70:
        for j in range(6):
            table[(i, j)].set_facecolor('#FFEBEE')

ax.set_title('Outage Scenario Statistics', fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('output/outage_scenario_comparison.png', dpi=150, bbox_inches='tight')
print("✅ Outage scenario comparison saved to: output/outage_scenario_comparison.png")

# Print summary
print("\n" + "=" * 70)
print("OUTAGE SCENARIO ANALYSIS")
print("=" * 70)

for scenario_name, file_path in outage_files.items():
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        df['month'] = (df['hour'] // 730) + 1
        df['month'] = df['month'].clip(1, 12)
        df['outage'] = ~df['grid_stable']
        
        total_outage = df['outage'].sum()
        winter_outage = df[df['month'].isin([1, 2, 12])]['outage'].sum()
        
        print(f"\n{scenario_name}:")
        print(f"  Total outage hours: {total_outage} ({total_outage/8760*100:.2f}% of year)")
        print(f"  Winter outage hours: {winter_outage} ({winter_outage/total_outage*100:.1f}% of all outages)")
        print(f"  Grid stability: {(1 - total_outage/8760)*100:.2f}%")

print("\n" + "=" * 70)
print("💡 RECOMMENDATION:")
print("=" * 70)
print("With severe winter outages, the 50% winter battery reserve is CRITICAL!")
print("It ensures you have 25,000 kWh available during the riskiest months.")
print("=" * 70)

plt.show()
