"""
Generate a CSV file simulating random Texas-style outages over a year (8760 hours).
Output columns: hour, grid_stable (True/False)
"""
import numpy as np
import pandas as pd

# Parameters
hours_per_year = 8760
num_long_outages = 2      # e.g., 2 major events
long_outage_min = 24      # min duration (hours)
long_outage_max = 72      # max duration (hours)
num_short_outages = 10    # e.g., 10 short events
short_outage_min = 2      # min duration (hours)
short_outage_max = 8      # max duration (hours)

np.random.seed(42)  # For reproducibility

grid = np.ones(hours_per_year, dtype=int)

# Place long outages
for _ in range(num_long_outages):
    start = np.random.randint(0, hours_per_year - long_outage_max)
    duration = np.random.randint(long_outage_min, long_outage_max + 1)
    grid[start:start+duration] = 0

# Place short outages
for _ in range(num_short_outages):
    start = np.random.randint(0, hours_per_year - short_outage_max)
    duration = np.random.randint(short_outage_min, short_outage_max + 1)
    grid[start:start+duration] = 0

# Convert to True/False
grid_bool = grid == 1

# Save to CSV with hour column and header
df = pd.DataFrame({
    'hour': np.arange(hours_per_year),
    'grid_stable': grid_bool
})
df.to_csv('input_data/grid_stability_random_texas.csv', index=False)
print('Random outage file saved as input_data/grid_stability_random_texas.csv (columns: hour, grid_stable)')
# Save to CSV
pd.Series(grid).to_csv('input_data/grid_stability_random_texas.csv', index=False, header=False)
print('Random outage file saved as input_data/grid_stability_random_texas.csv')
