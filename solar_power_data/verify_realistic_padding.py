import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import numpy as np

print("Creating comparison plot to show day-to-day variation...")

base_dir = Path(__file__).parent

# Load the realistic padded data
df = pd.read_csv(base_dir / "solar_data_full_year_realistic_padded.csv")
df['interval_start_local'] = pd.to_datetime(df['interval_start_local'], utc=True).dt.tz_convert('US/Central')
df['month'] = df['interval_start_local'].dt.month
df['day'] = df['interval_start_local'].dt.day

solar_col = 'cop_hsl_system_wide'

# Create figure
fig, axes = plt.subplots(3, 2, figsize=(16, 12))
fig.suptitle('Realistic Solar Data - Showing Day-to-Day Variations', fontsize=16, fontweight='bold')

# Plot 6 different months to show variation
months_to_plot = [
    (1, 'January (Winter)', 'blue'),
    (4, 'April (Spring)', 'green'),
    (6, 'June (Summer)', 'red'),
    (8, 'August (Summer)', 'orange'),
    (10, 'October (Fall)', 'brown'),
    (12, 'December (Winter)', 'navy')
]

for idx, (month, title, color) in enumerate(months_to_plot):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]
    
    # Get data for this month
    month_data = df[df['month'] == month]
    
    # Plot the time series
    ax.plot(month_data['interval_start_local'], month_data[solar_col], 
            linewidth=0.8, color=color, alpha=0.7)
    ax.fill_between(month_data['interval_start_local'], month_data[solar_col], 
                     alpha=0.2, color=color)
    
    # Mark original vs padded data
    original_cutoff = pd.Timestamp(f'2024-{month:02d}-11', tz='US/Central')
    if month in [1, 11]:  # Jan has 13 days, Nov has 11 days original
        original_cutoff = pd.Timestamp(f'2024-{month:02d}-14' if month == 1 else f'2024-{month:02d}-12', tz='US/Central')
    
    ax.axvline(original_cutoff, color='red', linestyle='--', linewidth=2, 
               alpha=0.5, label='Original | Padded')
    
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlabel('Day of Month', fontsize=10)
    ax.set_ylabel('Power (MW)', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
    ax.legend(loc='upper right', fontsize=8)
    
    # Calculate and display variation
    daily_totals = month_data.groupby('day')[solar_col].sum()
    cv = daily_totals.std() / daily_totals.mean() * 100
    ax.text(0.02, 0.98, f'Day-to-day variation: {cv:.1f}%', 
            transform=ax.transAxes, fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()

output_file = base_dir / "realistic_padding_verification.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✓ Verification plot saved to: {output_file.name}")

# Create a second plot comparing daily totals
fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Calculate daily totals
df['date'] = df['interval_start_local'].dt.date
daily_totals = df.groupby('date')[solar_col].sum() / 1000  # Convert to GWh

# Plot 1: Full year daily totals
dates = pd.to_datetime(list(daily_totals.index))
ax1.plot(dates, daily_totals.values, linewidth=1, color='darkgreen', alpha=0.7)
ax1.fill_between(dates, daily_totals.values, alpha=0.3, color='green')
ax1.set_title('Daily Total Energy Production - Full Year (with realistic variations)', 
              fontsize=13, fontweight='bold')
ax1.set_ylabel('Daily Energy (GWh)', fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# Add annotation showing variation
cv_full_year = daily_totals.std() / daily_totals.mean() * 100
ax1.text(0.02, 0.98, f'Year-round variation: {cv_full_year:.1f}%\n(Realistic weather variability)', 
         transform=ax1.transAxes, fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

# Plot 2: Zoom into June to show day-to-day detail
june_data = df[(df['month'] == 6)]
ax2.plot(june_data['interval_start_local'], june_data[solar_col], 
         linewidth=1.5, color='darkorange', alpha=0.8)
ax2.fill_between(june_data['interval_start_local'], june_data[solar_col], 
                 alpha=0.3, color='orange')

# Mark the transition
june_cutoff = pd.Timestamp('2024-06-11', tz='US/Central')
ax2.axvline(june_cutoff, color='red', linestyle='--', linewidth=2, alpha=0.7,
            label='Original data ends → Padded data begins')

ax2.set_title('June Detail - Showing Smooth Transition and Realistic Daily Variations', 
              fontsize=13, fontweight='bold')
ax2.set_xlabel('Date', fontsize=11)
ax2.set_ylabel('Power Output (MW)', fontsize=11)
ax2.grid(True, alpha=0.3)
ax2.legend(loc='upper right', fontsize=10)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

plt.tight_layout()

output_file2 = base_dir / "realistic_padding_detail.png"
plt.savefig(output_file2, dpi=300, bbox_inches='tight')
print(f"✓ Detail plot saved to: {output_file2.name}")

print("\n" + "="*80)
print("VISUALIZATION COMPLETE!")
print("="*80)
print("\nCreated files:")
print(f"  1. {output_file.name} - 6-month comparison showing variations")
print(f"  2. {output_file2.name} - Full year + June detail view")
print("\nThe padded data now shows realistic day-to-day variations")
print("similar to actual weather-dependent solar generation!")

plt.show()
