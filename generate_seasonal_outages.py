"""
Generate a CSV file simulating seasonal power outages over a year (8760 hours).
Winter months (December, January, February) have more frequent and longer outages.
Output columns: hour, grid_stable (True/False)
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import argparse


def generate_seasonal_outages(
    hours_per_year=8760,
    # Summer outages (Mar-Nov)
    summer_long_outages=2,
    summer_long_min=12,
    summer_long_max=48,
    summer_short_outages=5,
    summer_short_min=1,
    summer_short_max=6,
    # Winter outages (Dec-Feb)
    winter_long_outages=6,
    winter_long_min=24,
    winter_long_max=96,
    winter_short_outages=15,
    winter_short_min=2,
    winter_short_max=12,
    seed=42,
    output_file='input_data/grid_stability_seasonal.csv'
):
    """
    Generate seasonal outages with more frequent and longer outages in winter.
    
    Args:
        hours_per_year: Total hours to simulate (default 8760 for full year)
        summer_long_outages: Number of long outages during summer months
        summer_long_min: Minimum duration for summer long outages (hours)
        summer_long_max: Maximum duration for summer long outages (hours)
        summer_short_outages: Number of short outages during summer months
        summer_short_min: Minimum duration for summer short outages (hours)
        summer_short_max: Maximum duration for summer short outages (hours)
        winter_long_outages: Number of long outages during winter months
        winter_long_min: Minimum duration for winter long outages (hours)
        winter_long_max: Maximum duration for winter long outages (hours)
        winter_short_outages: Number of short outages during winter months
        winter_short_min: Minimum duration for winter short outages (hours)
        winter_short_max: Maximum duration for winter short outages (hours)
        seed: Random seed for reproducibility
        output_file: Output CSV file path
    """
    np.random.seed(seed)
    
    # Initialize grid as all stable
    grid = np.ones(hours_per_year, dtype=int)
    
    # Define winter and summer hours
    # Assume starting January 1st
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(hours=i) for i in range(hours_per_year)]
    months = [d.month for d in dates]
    
    # Winter months: December (12), January (1), February (2)
    winter_months = [12, 1, 2]
    winter_hours = [i for i, m in enumerate(months) if m in winter_months]
    summer_hours = [i for i, m in enumerate(months) if m not in winter_months]
    
    print(f"Total hours: {hours_per_year}")
    print(f"Winter hours: {len(winter_hours)} ({len(winter_hours)/hours_per_year*100:.1f}%)")
    print(f"Summer hours: {len(summer_hours)} ({len(summer_hours)/hours_per_year*100:.1f}%)")
    
    # Place summer outages
    print(f"\n📅 Summer Outages (Mar-Nov):")
    print(f"  Long outages: {summer_long_outages} × {summer_long_min}-{summer_long_max} hours")
    print(f"  Short outages: {summer_short_outages} × {summer_short_min}-{summer_short_max} hours")
    
    for _ in range(summer_long_outages):
        if len(summer_hours) > summer_long_max:
            start_idx = np.random.choice(summer_hours[:-summer_long_max])
            duration = np.random.randint(summer_long_min, summer_long_max + 1)
            grid[start_idx:start_idx+duration] = 0
    
    for _ in range(summer_short_outages):
        if len(summer_hours) > summer_short_max:
            start_idx = np.random.choice(summer_hours[:-summer_short_max])
            duration = np.random.randint(summer_short_min, summer_short_max + 1)
            grid[start_idx:start_idx+duration] = 0
    
    # Place winter outages
    print(f"\n❄️  Winter Outages (Dec-Feb):")
    print(f"  Long outages: {winter_long_outages} × {winter_long_min}-{winter_long_max} hours")
    print(f"  Short outages: {winter_short_outages} × {winter_short_min}-{winter_short_max} hours")
    
    for _ in range(winter_long_outages):
        if len(winter_hours) > winter_long_max:
            start_idx = np.random.choice(winter_hours[:-winter_long_max])
            duration = np.random.randint(winter_long_min, winter_long_max + 1)
            grid[start_idx:start_idx+duration] = 0
    
    for _ in range(winter_short_outages):
        if len(winter_hours) > winter_short_max:
            start_idx = np.random.choice(winter_hours[:-winter_short_max])
            duration = np.random.randint(winter_short_min, winter_short_max + 1)
            grid[start_idx:start_idx+duration] = 0
    
    # Convert to True/False
    grid_bool = grid == 1
    
    # Calculate statistics
    total_outage_hours = np.sum(grid == 0)
    winter_outage_hours = np.sum([grid[i] == 0 for i in winter_hours])
    summer_outage_hours = np.sum([grid[i] == 0 for i in summer_hours])
    
    print(f"\n📊 Outage Statistics:")
    print(f"  Total outage hours: {total_outage_hours} ({total_outage_hours/hours_per_year*100:.2f}%)")
    print(f"  Winter outage hours: {winter_outage_hours} ({winter_outage_hours/len(winter_hours)*100:.2f}% of winter)")
    print(f"  Summer outage hours: {summer_outage_hours} ({summer_outage_hours/len(summer_hours)*100:.2f}% of summer)")
    print(f"  Winter/Summer ratio: {winter_outage_hours/max(summer_outage_hours,1):.1f}x more outages in winter")
    
    # Save to CSV with hour column and header
    df = pd.DataFrame({
        'hour': np.arange(hours_per_year),
        'grid_stable': grid_bool
    })
    df.to_csv(output_file, index=False)
    print(f"\n✅ Seasonal outage file saved as: {output_file}")
    print(f"   Columns: hour, grid_stable (True/False)")
    
    return df


def main():
    parser = argparse.ArgumentParser(
        description='Generate seasonal power outage data with more frequent outages in winter.'
    )
    parser.add_argument('--output', type=str, 
                       default='input_data/grid_stability_seasonal.csv',
                       help='Output CSV file path')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility')
    parser.add_argument('--profile', type=str, default='moderate',
                       choices=['mild', 'moderate', 'severe', 'extreme'],
                       help='Severity profile for winter outages')
    
    args = parser.parse_args()
    
    # Define outage profiles
    profiles = {
        'mild': {
            'summer_long_outages': 1,
            'summer_long_min': 6,
            'summer_long_max': 24,
            'summer_short_outages': 3,
            'summer_short_min': 1,
            'summer_short_max': 4,
            'winter_long_outages': 3,
            'winter_long_min': 12,
            'winter_long_max': 48,
            'winter_short_outages': 8,
            'winter_short_min': 2,
            'winter_short_max': 8,
        },
        'moderate': {
            'summer_long_outages': 2,
            'summer_long_min': 12,
            'summer_long_max': 48,
            'summer_short_outages': 5,
            'summer_short_min': 1,
            'summer_short_max': 6,
            'winter_long_outages': 6,
            'winter_long_min': 24,
            'winter_long_max': 96,
            'winter_short_outages': 15,
            'winter_short_min': 2,
            'winter_short_max': 12,
        },
        'severe': {
            'summer_long_outages': 3,
            'summer_long_min': 18,
            'summer_long_max': 60,
            'summer_short_outages': 8,
            'summer_short_min': 2,
            'summer_short_max': 8,
            'winter_long_outages': 10,
            'winter_long_min': 36,
            'winter_long_max': 120,
            'winter_short_outages': 25,
            'winter_short_min': 3,
            'winter_short_max': 16,
        },
        'extreme': {
            'summer_long_outages': 4,
            'summer_long_min': 24,
            'summer_long_max': 72,
            'summer_short_outages': 12,
            'summer_short_min': 2,
            'summer_short_max': 10,
            'winter_long_outages': 15,
            'winter_long_min': 48,
            'winter_long_max': 168,  # Up to 1 week
            'winter_short_outages': 35,
            'winter_short_min': 4,
            'winter_short_max': 20,
        }
    }
    
    print("=" * 70)
    print(f"Generating Seasonal Power Outages - {args.profile.upper()} Profile")
    print("=" * 70)
    
    profile_params = profiles[args.profile]
    generate_seasonal_outages(
        seed=args.seed,
        output_file=args.output,
        **profile_params
    )
    
    print("\n" + "=" * 70)
    print("Generation Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
