"""
Generate sample input CSV files for the energy system simulation.
"""

import numpy as np
import pandas as pd
from pathlib import Path


def generate_sample_data(num_days: int = 7, samples_per_day: int = 24, 
                        output_dir: str = "input_data"):
    """
    Generate sample input CSV files.
    
    Args:
        num_days: Number of days to simulate
        samples_per_day: Number of samples per day (default 24 = hourly)
        output_dir: Directory to save CSV files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    num_samples = num_days * samples_per_day
    hours = np.arange(num_samples)
    
    # Generate solar irradiation data (W/m²)
    # Simulate daily solar cycle with some variation
    irradiation = []
    for day in range(num_days):
        for hour in range(samples_per_day):
            # Simple sinusoidal model for solar irradiation
            # Peak at noon (hour 12), zero at night
            if 6 <= hour < 20:  # Daylight hours
                time_factor = np.sin(np.pi * (hour - 6) / 14)
                base_irradiation = 800 * time_factor  # Max ~800 W/m²
                # Add some random variation (clouds, weather)
                noise = np.random.normal(0, 50)
                irradiation.append(max(0, base_irradiation + noise))
            else:
                irradiation.append(0)
    
    irradiation_df = pd.DataFrame({
        'hour': hours,
        'irradiation_w_m2': irradiation
    })
    irradiation_file = output_path / "solar_irradiation.csv"
    irradiation_df.to_csv(irradiation_file, index=False)
    print(f"Created {irradiation_file}")
    
    # Generate load consumption data (kW)
    # Simulate prison load profile with base load and peaks
    load = []
    for day in range(num_days):
        for hour in range(samples_per_day):
            # Base load (lighting, refrigeration, etc.)
            base_load = 50
            
            # Morning peak (6-9 AM)
            if 6 <= hour < 9:
                peak_load = 30 * (1 + np.sin(np.pi * (hour - 6) / 3))
            # Evening peak (17-22 PM)
            elif 17 <= hour < 22:
                peak_load = 40 * (1 + np.sin(np.pi * (hour - 17) / 5))
            else:
                peak_load = 0
            
            # Add some random variation
            noise = np.random.normal(0, 5)
            total_load = base_load + peak_load + noise
            load.append(max(10, total_load))  # Minimum 10 kW
    
    load_df = pd.DataFrame({
        'hour': hours,
        'load_kw': load
    })
    load_file = output_path / "load_consumption.csv"
    load_df.to_csv(load_file, index=False)
    print(f"Created {load_file}")
    
    # Generate grid stability data
    # Simulate unstable grid with random outages
    grid_stable = []
    for day in range(num_days):
        for hour in range(samples_per_day):
            # 90% stable, 10% unstable
            # Simulate occasional outages lasting 1-3 hours
            if np.random.random() < 0.95:  # 95% chance of stable
                grid_stable.append(True)
            else:
                grid_stable.append(False)
    
    grid_df = pd.DataFrame({
        'hour': hours,
        'grid_stable': grid_stable
    })
    grid_file = output_path / "grid_stability.csv"
    grid_df.to_csv(grid_file, index=False)
    print(f"Created {grid_file}")
    
    return irradiation_file, load_file, grid_file


if __name__ == "__main__":
    print("Generating sample input data...")
    generate_sample_data(num_days=7, samples_per_day=24)
    print("\nSample data generated successfully!")
    print("Files created in 'input_data' directory:")
    print("  - solar_irradiation.csv")
    print("  - load_consumption.csv")
    print("  - grid_stability.csv")
