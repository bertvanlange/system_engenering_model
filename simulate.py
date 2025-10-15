"""
Main simulation script for the energy system.
"""

import argparse
from pathlib import Path
import pandas as pd
from energy_system import EnergySystem, load_input_data
from generate_input_data import generate_sample_data


def run_simulation(irradiation_file: str, load_file: str, grid_stability_file: str,
                  pv_peak_kw: float = 100.0, battery_capacity_kwh: float = 200.0,
                  battery_efficiency: float = 0.95, battery_self_discharge: float = 0.0001,
                  timestep_hours: float = 1.0, output_dir: str = "output"):
    """
    Run the energy system simulation.
    
    Args:
        irradiation_file: Path to solar irradiation CSV
        load_file: Path to load consumption CSV
        grid_stability_file: Path to grid stability CSV
        pv_peak_kw: PV system peak power in kW
        battery_capacity_kwh: Battery capacity in kWh
        battery_efficiency: Battery charge/discharge efficiency
        battery_self_discharge: Battery self-discharge rate per time step
        timestep_hours: Time step duration in hours
        output_dir: Directory to save output files
    """
    print("=" * 60)
    print("Energy System Simulation")
    print("=" * 60)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load input data
    print("\nLoading input data...")
    print(f"  Solar irradiation: {irradiation_file}")
    print(f"  Load consumption: {load_file}")
    print(f"  Grid stability: {grid_stability_file}")
    
    data = load_input_data(irradiation_file, load_file, grid_stability_file)
    print(f"  Loaded {len(data)} time steps")
    
    # Initialize energy system
    print("\nInitializing energy system...")
    print(f"  PV peak power: {pv_peak_kw} kW")
    print(f"  Battery capacity: {battery_capacity_kwh} kWh")
    print(f"  Battery efficiency: {battery_efficiency * 100}%")
    print(f"  Battery self-discharge: {battery_self_discharge * 100}% per time step")
    
    system = EnergySystem(
        pv_peak_kw=pv_peak_kw,
        battery_capacity_kwh=battery_capacity_kwh,
        battery_efficiency=battery_efficiency,
        battery_self_discharge=battery_self_discharge
    )
    
    # Run simulation
    print("\nRunning simulation...")
    results = system.simulate(data, timestep_hours=timestep_hours)
    
    # Save results
    results_file = output_path / "simulation_results.csv"
    results.to_csv(results_file)
    print(f"\nResults saved to: {results_file}")
    
    # Calculate summary statistics
    print("\n" + "=" * 60)
    print("Simulation Summary")
    print("=" * 60)
    
    total_pv_generation = results['pv_generation_kwh'].sum()
    total_load = results['load_kwh'].sum()
    total_grid_import = results['grid_import'].sum()
    total_grid_export = results['grid_export'].sum()
    avg_self_sufficiency = results['self_sufficiency'].mean()
    total_unmet_load = results['unmet_load'].sum()
    
    print(f"\nTotal PV generation: {total_pv_generation:.2f} kWh")
    print(f"Total load consumption: {total_load:.2f} kWh")
    print(f"Total grid import: {total_grid_import:.2f} kWh")
    print(f"Total grid export: {total_grid_export:.2f} kWh")
    print(f"Net grid energy: {total_grid_import - total_grid_export:.2f} kWh")
    print(f"Average self-sufficiency: {avg_self_sufficiency * 100:.2f}%")
    print(f"Total unmet load: {total_unmet_load:.2f} kWh")
    
    battery_cycles = results['battery_soc'].diff().abs().sum() / 2
    print(f"\nBattery charge/discharge cycles: {battery_cycles:.2f}")
    print(f"Final battery SOC: {results['battery_soc'].iloc[-1] * 100:.2f}%")
    
    grid_stable_ratio = data['grid_stable'].sum() / len(data)
    print(f"\nGrid stability: {grid_stable_ratio * 100:.2f}%")
    
    # Create visualization
    print("\nGenerating plots...")
    plot_file = output_path / "simulation_results.png"
    system.plot_results(results, save_path=str(plot_file))
    print(f"Plots saved to: {plot_file}")
    
    print("\n" + "=" * 60)
    print("Simulation completed successfully!")
    print("=" * 60)
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Energy System Simulation with PV, Battery, Load, and Grid"
    )
    
    # Input files
    parser.add_argument(
        '--irradiation', 
        type=str, 
        default='input_data/solar_irradiation.csv',
        help='Path to solar irradiation CSV file'
    )
    parser.add_argument(
        '--load', 
        type=str, 
        default='input_data/load_consumption.csv',
        help='Path to load consumption CSV file'
    )
    parser.add_argument(
        '--grid', 
        type=str, 
        default='input_data/grid_stability.csv',
        help='Path to grid stability CSV file'
    )
    
    # System parameters
    parser.add_argument(
        '--pv-peak', 
        type=float, 
        default=100.0,
        help='PV system peak power in kW (default: 100.0)'
    )
    parser.add_argument(
        '--battery-capacity', 
        type=float, 
        default=200.0,
        help='Battery capacity in kWh (default: 200.0)'
    )
    parser.add_argument(
        '--battery-efficiency', 
        type=float, 
        default=0.95,
        help='Battery efficiency 0-1 (default: 0.95)'
    )
    parser.add_argument(
        '--battery-self-discharge', 
        type=float, 
        default=0.0001,
        help='Battery self-discharge rate per time step (default: 0.0001)'
    )
    parser.add_argument(
        '--timestep', 
        type=float, 
        default=1.0,
        help='Time step duration in hours (default: 1.0)'
    )
    
    # Output
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='output',
        help='Output directory for results (default: output)'
    )
    
    # Generate sample data option
    parser.add_argument(
        '--generate-sample-data',
        action='store_true',
        help='Generate sample input data before running simulation'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days for sample data generation (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Generate sample data if requested
    if args.generate_sample_data:
        print("Generating sample input data...")
        generate_sample_data(num_days=args.days, samples_per_day=24)
        print()
    
    # Check if input files exist
    input_files = [args.irradiation, args.load, args.grid]
    missing_files = [f for f in input_files if not Path(f).exists()]
    
    if missing_files:
        print("Error: Input files not found:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nUse --generate-sample-data to create sample input files.")
        return
    
    # Run simulation
    run_simulation(
        irradiation_file=args.irradiation,
        load_file=args.load,
        grid_stability_file=args.grid,
        pv_peak_kw=args.pv_peak,
        battery_capacity_kwh=args.battery_capacity,
        battery_efficiency=args.battery_efficiency,
        battery_self_discharge=args.battery_self_discharge,
        timestep_hours=args.timestep,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
