"""
Example scenarios for the energy system simulation.
"""

from energy_system import EnergySystem
from generate_input_data import generate_sample_data
import pandas as pd
import numpy as np


def scenario_high_pv():
    """Scenario with high PV capacity."""
    print("\n" + "=" * 60)
    print("Scenario 1: High PV Capacity (150 kW)")
    print("=" * 60)
    
    # Generate data
    generate_sample_data(num_days=3, samples_per_day=24, output_dir="input_data")
    
    # Load data
    data = pd.DataFrame({
        'irradiation_w_m2': pd.read_csv('input_data/solar_irradiation.csv')['irradiation_w_m2'],
        'load_kw': pd.read_csv('input_data/load_consumption.csv')['load_kw'],
        'grid_stable': pd.read_csv('input_data/grid_stability.csv')['grid_stable'].astype(bool)
    })
    
    # Run simulation with high PV
    system = EnergySystem(pv_peak_kw=150, battery_capacity_kwh=200)
    results = system.simulate(data)
    
    print(f"Average self-sufficiency: {results['self_sufficiency'].mean() * 100:.2f}%")
    print(f"Total grid export: {results['grid_export'].sum():.2f} kWh")
    print(f"Total grid import: {results['grid_import'].sum():.2f} kWh")


def scenario_large_battery():
    """Scenario with large battery capacity."""
    print("\n" + "=" * 60)
    print("Scenario 2: Large Battery Capacity (400 kWh)")
    print("=" * 60)
    
    # Load data
    data = pd.DataFrame({
        'irradiation_w_m2': pd.read_csv('input_data/solar_irradiation.csv')['irradiation_w_m2'],
        'load_kw': pd.read_csv('input_data/load_consumption.csv')['load_kw'],
        'grid_stable': pd.read_csv('input_data/grid_stability.csv')['grid_stable'].astype(bool)
    })
    
    # Run simulation with large battery
    system = EnergySystem(pv_peak_kw=100, battery_capacity_kwh=400)
    results = system.simulate(data)
    
    print(f"Average self-sufficiency: {results['self_sufficiency'].mean() * 100:.2f}%")
    print(f"Final battery SOC: {results['battery_soc'].iloc[-1] * 100:.2f}%")
    print(f"Battery cycles: {results['battery_soc'].diff().abs().sum() / 2:.2f}")


def scenario_unstable_grid():
    """Scenario with highly unstable grid."""
    print("\n" + "=" * 60)
    print("Scenario 3: Unstable Grid (50% stability)")
    print("=" * 60)
    
    # Load data
    irr_data = pd.read_csv('input_data/solar_irradiation.csv')
    load_data = pd.read_csv('input_data/load_consumption.csv')
    
    # Create unstable grid scenario
    num_samples = len(irr_data)
    grid_stable = np.random.choice([True, False], size=num_samples, p=[0.5, 0.5])
    
    data = pd.DataFrame({
        'irradiation_w_m2': irr_data['irradiation_w_m2'],
        'load_kw': load_data['load_kw'],
        'grid_stable': grid_stable
    })
    
    # Run simulation
    system = EnergySystem(pv_peak_kw=100, battery_capacity_kwh=200)
    results = system.simulate(data)
    
    print(f"Grid stability: {data['grid_stable'].mean() * 100:.2f}%")
    print(f"Average self-sufficiency: {results['self_sufficiency'].mean() * 100:.2f}%")
    print(f"Total unmet load: {results['unmet_load'].sum():.2f} kWh")
    print(f"Unmet load events: {(results['unmet_load'] > 0).sum()} times")


def scenario_comparison():
    """Compare different system configurations."""
    print("\n" + "=" * 60)
    print("Scenario 4: System Configuration Comparison")
    print("=" * 60)
    
    # Load data
    data = pd.DataFrame({
        'irradiation_w_m2': pd.read_csv('input_data/solar_irradiation.csv')['irradiation_w_m2'],
        'load_kw': pd.read_csv('input_data/load_consumption.csv')['load_kw'],
        'grid_stable': pd.read_csv('input_data/grid_stability.csv')['grid_stable'].astype(bool)
    })
    
    configs = [
        ("Small System", 50, 100),
        ("Medium System", 100, 200),
        ("Large System", 150, 300),
        ("Very Large System", 200, 400)
    ]
    
    print("\nConfiguration Comparison:")
    print("-" * 80)
    print(f"{'Configuration':<20} {'PV (kW)':<10} {'Battery (kWh)':<15} {'Self-Suff %':<15} {'Net Grid (kWh)':<15}")
    print("-" * 80)
    
    for name, pv_kw, battery_kwh in configs:
        system = EnergySystem(pv_peak_kw=pv_kw, battery_capacity_kwh=battery_kwh)
        results = system.simulate(data)
        self_suff = results['self_sufficiency'].mean() * 100
        net_grid = results['net_grid'].sum()
        print(f"{name:<20} {pv_kw:<10} {battery_kwh:<15} {self_suff:<15.2f} {net_grid:<15.2f}")


if __name__ == "__main__":
    print("Energy System Simulation - Example Scenarios")
    
    # Run scenarios
    scenario_high_pv()
    scenario_large_battery()
    scenario_unstable_grid()
    scenario_comparison()
    
    print("\n" + "=" * 60)
    print("All scenarios completed!")
    print("=" * 60)
