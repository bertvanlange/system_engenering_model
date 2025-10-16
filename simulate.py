"""
Main simulation script for the energy system.
"""

import argparse
from pathlib import Path
import pandas as pd
import yaml
from energy_system import EnergySystem, load_input_data
from generate_input_data import generate_sample_data


def run_simulation(irradiation_file: str, load_file: str, grid_stability_file: str,
                  pv_peak_kw: float = 100.0, battery_capacity_kwh: float = 200.0,
                  battery_efficiency: float = 0.95, battery_self_discharge: float = 0.0001,
                  timestep_hours: float = 1.0, output_dir: str = "output",
                  start_index: int = 0, values_only: bool = False,
                  config: dict = None):
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
    

    # If config is provided, override all file paths and parameters
    if config is not None:
        print("\nLoading configuration from config file...")
        irradiation_file = config.get('solar_file', irradiation_file)
        load_file = config.get('load_file', load_file)
        grid_stability_file = config.get('outage_file', grid_stability_file)
        pv_peak_kw = config.get('pv_peak_kw', pv_peak_kw)
        battery_capacity_kwh = config.get('battery_capacity_kwh', battery_capacity_kwh)
        battery_efficiency = config.get('battery_efficiency', battery_efficiency)
        battery_self_discharge = config.get('battery_self_discharge', battery_self_discharge)
        timestep_hours = config.get('timestep_hours', timestep_hours)
        output_dir = config.get('output_dir', output_dir)
        start_index = config.get('start_index', start_index)
        values_only = config.get('values_only', True)
        # New: targets for scaling
        target_pv_peak_kw = config.get('target_pv_peak_kw', None)
        target_annual_load_kwh = config.get('target_annual_load_kwh', None)
        # Fallback to manual scale factors if targets not set
        solar_scale_factor = config.get('solar_scale_factor', 1.0)
        load_scale_factor = config.get('load_scale_factor', 1.0)
        # Date range for simulation
        start_date = config.get('start_date', None)
        end_date = config.get('end_date', None)
    else:
        target_pv_peak_kw = None
        target_annual_load_kwh = None
        solar_scale_factor = 1.0
        load_scale_factor = 1.0
        start_date = None
        end_date = None
    # Load input data
    print("\nLoading input data...")
    if values_only:
        print(f"  Using values-only input files:")
        print(f"    Solar: {irradiation_file}")
        print(f"    Load: {load_file}")
        print(f"    Outages: {grid_stability_file}")
        
        # Load solar (no header)
        irradiation = pd.read_csv(irradiation_file, header=None).iloc[:, 0]
        
        # Load load file - check if it has headers
        load_df = pd.read_csv(load_file)
        if 'load_kw' in load_df.columns:
            load = load_df['load_kw'].values
        elif 'hour' in load_df.columns and len(load_df.columns) > 1:
            load = load_df.iloc[:, 1].values
        else:
            # No header, read as values only
            load = pd.read_csv(load_file, header=None).iloc[:, 0].values
        
        # Load grid file - check if it has headers
        grid_df = pd.read_csv(grid_stability_file)
        if 'grid_stable' in grid_df.columns:
            grid = grid_df['grid_stable'].values
        elif 'hour' in grid_df.columns and len(grid_df.columns) > 1:
            grid = grid_df.iloc[:, 1].values
        else:
            # No header, read as values only
            grid = pd.read_csv(grid_stability_file, header=None).iloc[:, 0].values

        # --- Scaling logic ---
        # Solar: scale so that sum(irradiation) * pv_peak_kw = target annual generation (if target_pv_peak_kw is set)
        if target_pv_peak_kw is not None:
            # Assume 1.0 in irradiation means full PV peak for 1 hour
            # So total annual generation = sum(irradiation) * target_pv_peak_kw
            # We want to scale irradiation so that sum(irradiation) * target_pv_peak_kw = sum(irradiation_raw) * pv_peak_kw * solar_scale_factor (if solar_scale_factor is set)
            # But user wants to define the PV size, so scale irradiation so that the PV peak in simulation matches target_pv_peak_kw
            pv_peak_kw = target_pv_peak_kw
            # If the irradiation values are already normalized (max=1), no scaling needed except for PV peak
            # But if user wants to scale the irradiation profile to match a certain total, do:
            # (If you want to scale the irradiation so that the total annual generation matches a target, use this:)
            # If you want to keep the shape but change the total, scale by ratio
            # But here, we just set pv_peak_kw, so the rest of the code will use it
        if target_annual_load_kwh is not None:
            # Scale load so that sum(load) * timestep_hours = target_annual_load_kwh
            current_annual_load = load.sum() * timestep_hours
            if current_annual_load > 0:
                load_scale_factor = target_annual_load_kwh / current_annual_load
                print(f"  Scaling load: current annual={current_annual_load:.2f} kWh, target={target_annual_load_kwh:.2f} kWh, factor={load_scale_factor:.4f}")
                load = load * load_scale_factor
        # If solar_scale_factor is set and no target_pv_peak_kw, apply it
        if solar_scale_factor != 1.0 and target_pv_peak_kw is None:
            irradiation = irradiation * solar_scale_factor
        # If load_scale_factor is set and no target_annual_load_kwh, apply it
        if load_scale_factor != 1.0 and target_annual_load_kwh is None:
            load = load * load_scale_factor

        # Ensure all arrays have the same length
        min_length = min(len(irradiation), len(load), len(grid))
        if len(irradiation) != len(load) or len(irradiation) != len(grid):
            print(f"  Warning: Input files have different lengths (solar={len(irradiation)}, load={len(load)}, grid={len(grid)})")
            print(f"  Trimming all to minimum length: {min_length}")
            irradiation = irradiation[:min_length]
            load = load[:min_length]
            grid = grid[:min_length]

        data = pd.DataFrame({
            'irradiation_w_m2': irradiation,
            'load_kw': load,
            'grid_stable': grid,
        })
    else:
        print(f"  Solar irradiation: {irradiation_file}")
        print(f"  Load consumption: {load_file}")
        print(f"  Grid stability: {grid_stability_file}")
        data = load_input_data(irradiation_file, load_file, grid_stability_file)
        # Optionally scale if not values_only (for completeness)
        data['irradiation_w_m2'] = data['irradiation_w_m2'] * solar_scale_factor
        data['load_kw'] = data['load_kw'] * load_scale_factor
    print(f"  Loaded {len(data)} time steps")

    # Handle date range if specified (convert dates to hour indices)
    if start_date is not None or end_date is not None:
        from datetime import datetime
        # Assume year starts at hour 0 = Jan 1, 00:00
        year_start = datetime(2024, 1, 1)  # Use 2024 as reference (leap year with 8784 hours)
        
        if start_date is not None:
            # Convert to string if it's already a date object
            if not isinstance(start_date, str):
                start_date = start_date.strftime('%Y-%m-%d')
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            start_index = int((start_dt - year_start).total_seconds() / 3600)
            print(f"  Start date: {start_date} (hour {start_index})")
        
        if end_date is not None:
            # Convert to string if it's already a date object
            if not isinstance(end_date, str):
                end_date = end_date.strftime('%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_index = int((end_dt - year_start).total_seconds() / 3600)
            print(f"  End date: {end_date} (hour {end_index})")
            data = data.iloc[start_index:end_index].reset_index(drop=True)
        else:
            data = data.iloc[start_index:].reset_index(drop=True)
        
        print(f"  Simulation period: {len(data)} hours")
    elif start_index > 0:
        print(f"  Slicing data from start index: {start_index}")
        data = data.iloc[start_index:].reset_index(drop=True)
    
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

    parser.add_argument('--config', type=str, default=None, help='Path to YAML config file')

    # Retain all previous arguments for backward compatibility
    parser.add_argument('--irradiation', type=str, default='input_data/solar_irradiation.csv', help='Path to solar irradiation CSV file')
    parser.add_argument('--load', type=str, default='input_data/load_consumption.csv', help='Path to load consumption CSV file')
    parser.add_argument('--grid', type=str, default='input_data/grid_stability.csv', help='Path to grid stability CSV file')
    parser.add_argument('--pv-peak', type=float, default=100.0, help='PV system peak power in kW (default: 100.0)')
    parser.add_argument('--battery-capacity', type=float, default=200.0, help='Battery capacity in kWh (default: 200.0)')
    parser.add_argument('--battery-efficiency', type=float, default=0.95, help='Battery efficiency 0-1 (default: 0.95)')
    parser.add_argument('--battery-self-discharge', type=float, default=0.0001, help='Battery self-discharge rate per time step (default: 0.0001)')
    parser.add_argument('--timestep', type=float, default=1.0, help='Time step duration in hours (default: 1.0)')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory for results (default: output)')
    parser.add_argument('--generate-sample-data', action='store_true', help='Generate sample input data before running simulation')
    parser.add_argument('--days', type=int, default=7, help='Number of days for sample data generation (default: 7)')
    parser.add_argument('--values-only', action='store_true', help='Set if the irradiation file contains only values (no header, no timestamps)')
    parser.add_argument('--start-index', type=int, default=0, help='Start simulation from this time index (default: 0)')

    args = parser.parse_args()

    # If config file is provided, load it
    config = None
    if args.config:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)

    # Generate sample data if requested
    if args.generate_sample_data:
        print("Generating sample input data...")
        generate_sample_data(num_days=args.days, samples_per_day=24)
        print()

    # If using config, check files from config; else, use args
    if config is not None:
        input_files = [
            config.get('solar_file', args.irradiation),
            config.get('load_file', args.load),
            config.get('outage_file', args.grid)
        ]
    else:
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
        output_dir=args.output_dir,
        start_index=args.start_index,
        values_only=args.values_only,
        config=config
    )


if __name__ == "__main__":
    main()
