"""
Energy System Simulation Model
Simulates an energy system with solar panels (PV), battery, load, and grid connection.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict
import matplotlib.pyplot as plt
from pathlib import Path


class Battery:
    """Battery model with efficiency and self-discharge."""
    
    def __init__(self, capacity_kwh: float, efficiency: float = 0.95, 
                 self_discharge_rate: float = 0.0001, initial_soc: float = 0.5):
        """
        Initialize battery.
        
        Args:
            capacity_kwh: Battery capacity in kWh
            efficiency: Charge/discharge efficiency (0-1)
            self_discharge_rate: Self-discharge rate per time step (0-1)
            initial_soc: Initial state of charge (0-1)
        """
        self.capacity_kwh = capacity_kwh
        self.efficiency = efficiency
        self.self_discharge_rate = self_discharge_rate
        self.soc = initial_soc  # State of charge (0-1)
        self.energy_kwh = self.soc * self.capacity_kwh
        
    def charge(self, energy_kwh: float, timestep_hours: float = 1.0) -> float:
        """
        Charge the battery.
        
        Args:
            energy_kwh: Energy to charge in kWh
            timestep_hours: Time step duration in hours
            
        Returns:
            Actual energy charged in kWh
        """
        # Apply efficiency and capacity constraints
        max_charge = (self.capacity_kwh - self.energy_kwh) / self.efficiency
        actual_charge = min(energy_kwh, max_charge)
        self.energy_kwh += actual_charge * self.efficiency
        return actual_charge
    
    def discharge(self, energy_kwh: float, timestep_hours: float = 1.0) -> float:
        """
        Discharge the battery.
        
        Args:
            energy_kwh: Energy to discharge in kWh
            timestep_hours: Time step duration in hours
            
        Returns:
            Actual energy discharged in kWh
        """
        # Apply efficiency and capacity constraints
        max_discharge = self.energy_kwh * self.efficiency
        actual_discharge = min(energy_kwh, max_discharge)
        self.energy_kwh -= actual_discharge / self.efficiency
        return actual_discharge
    
    def apply_self_discharge(self, timestep_hours: float = 1.0):
        """Apply self-discharge for the time step."""
        self.energy_kwh *= (1 - self.self_discharge_rate * timestep_hours)
        
    def get_soc(self) -> float:
        """Get current state of charge (0-1)."""
        self.soc = self.energy_kwh / self.capacity_kwh
        return self.soc


class PVSystem:
    """Photovoltaic (solar panel) system model."""
    
    def __init__(self, peak_power_kw: float, efficiency: float = 0.20):
        """
        Initialize PV system.
        
        Args:
            peak_power_kw: Peak power in kW
            efficiency: PV panel efficiency (0-1)
        """
        self.peak_power_kw = peak_power_kw
        self.efficiency = efficiency
        
    def generate_power(self, irradiation_w_m2: float) -> float:
        """
        Calculate PV power generation.
        
        Args:
            irradiation_w_m2: Solar irradiation in W/m²
            
        Returns:
            Generated power in kW
        """
        # Standard test conditions: 1000 W/m²
        return (irradiation_w_m2 / 1000.0) * self.peak_power_kw


class EnergySystem:
    """Complete energy system simulation."""
    
    def __init__(self, pv_peak_kw: float, battery_capacity_kwh: float,
                 battery_efficiency: float = 0.95, battery_self_discharge: float = 0.0001):
        """
        Initialize energy system.
        
        Args:
            pv_peak_kw: PV system peak power in kW
            battery_capacity_kwh: Battery capacity in kWh
            battery_efficiency: Battery efficiency (0-1)
            battery_self_discharge: Battery self-discharge rate per time step
        """
        self.pv = PVSystem(pv_peak_kw)
        self.battery = Battery(battery_capacity_kwh, battery_efficiency, battery_self_discharge)
        self.results = []
        
    def simulate_timestep(self, irradiation_w_m2: float, load_kw: float, 
                         grid_stable: bool, timestep_hours: float = 1.0) -> Dict:
        """
        Simulate one time step of the energy system.
        
        Energy flow priority:
        1. PV -> Load
        2. PV excess -> Battery
        3. Battery -> Load (if PV insufficient)
        4. Grid -> Load (if PV + Battery insufficient)
        5. PV/Battery excess -> Grid
        
        Args:
            irradiation_w_m2: Solar irradiation in W/m²
            load_kw: Load power demand in kW
            grid_stable: Whether grid is stable
            timestep_hours: Time step duration in hours
            
        Returns:
            Dictionary with timestep results
        """
        # Generate PV power
        pv_power_kw = self.pv.generate_power(irradiation_w_m2)
        pv_energy_kwh = pv_power_kw * timestep_hours
        
        # Load energy demand
        load_energy_kwh = load_kw * timestep_hours
        
        # Initialize energy flows
        pv_to_load = 0
        pv_to_battery = 0
        pv_to_grid = 0
        battery_to_load = 0
        grid_to_load = 0
        battery_to_grid = 0
        
        # Step 1: PV feeds load first
        pv_to_load = min(pv_energy_kwh, load_energy_kwh)
        remaining_load = load_energy_kwh - pv_to_load
        remaining_pv = pv_energy_kwh - pv_to_load
        
        # Step 2: If PV excess, charge battery
        if remaining_pv > 0:
            pv_to_battery = self.battery.charge(remaining_pv, timestep_hours)
            remaining_pv -= pv_to_battery
            
        # Step 3: If load not satisfied, discharge battery
        if remaining_load > 0:
            battery_to_load = self.battery.discharge(remaining_load, timestep_hours)
            remaining_load -= battery_to_load
            
        # Step 4: If load still not satisfied and grid is stable, import from grid
        if remaining_load > 0 and grid_stable:
            grid_to_load = remaining_load
            remaining_load = 0
            
        # Step 5: If PV excess remains and grid is stable, export to grid
        if remaining_pv > 0 and grid_stable:
            pv_to_grid = remaining_pv
            remaining_pv = 0
            
        # Apply battery self-discharge
        self.battery.apply_self_discharge(timestep_hours)
        
        # Calculate metrics
        grid_import = grid_to_load
        grid_export = pv_to_grid + battery_to_grid
        net_grid = grid_import - grid_export
        
        # Self-sufficiency: fraction of load met by local generation
        local_supply = pv_to_load + battery_to_load
        self_sufficiency = local_supply / load_energy_kwh if load_energy_kwh > 0 else 1.0
        
        result = {
            'pv_generation_kwh': pv_energy_kwh,
            'load_kwh': load_energy_kwh,
            'battery_soc': self.battery.get_soc(),
            'battery_energy_kwh': self.battery.energy_kwh,
            'pv_to_load': pv_to_load,
            'pv_to_battery': pv_to_battery,
            'pv_to_grid': pv_to_grid,
            'battery_to_load': battery_to_load,
            'grid_to_load': grid_to_load,
            'grid_import': grid_import,
            'grid_export': grid_export,
            'net_grid': net_grid,
            'self_sufficiency': self_sufficiency,
            'grid_stable': grid_stable,
            'unmet_load': remaining_load
        }
        
        self.results.append(result)
        return result
    
    def simulate(self, data: pd.DataFrame, timestep_hours: float = 1.0) -> pd.DataFrame:
        """
        Run full simulation.
        
        Args:
            data: DataFrame with columns: 'irradiation_w_m2', 'load_kw', 'grid_stable'
            timestep_hours: Time step duration in hours
            
        Returns:
            DataFrame with simulation results
        """
        self.results = []
        
        for idx, row in data.iterrows():
            self.simulate_timestep(
                row['irradiation_w_m2'],
                row['load_kw'],
                row['grid_stable'],
                timestep_hours
            )
        
        results_df = pd.DataFrame(self.results)
        results_df.index = data.index
        return results_df
    
    def plot_results(self, results_df: pd.DataFrame, save_path: str = None):
        """
        Create visualization of simulation results.
        
        Args:
            results_df: DataFrame with simulation results
            save_path: Optional path to save figure
        """
        fig, axes = plt.subplots(5, 1, figsize=(12, 14))
        fig.suptitle('Energy System Simulation Results', fontsize=16, fontweight='bold')
        
        # Plot 1: PV Generation and Load
        ax = axes[0]
        ax.plot(results_df.index, results_df['pv_generation_kwh'], 
                label='PV Generation', color='orange', linewidth=2)
        ax.plot(results_df.index, results_df['load_kwh'], 
                label='Load', color='red', linewidth=2)
        ax.set_ylabel('Energy (kWh)', fontsize=11)
        ax.set_title('PV Generation and Load', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Plot 2: Battery State of Charge
        ax = axes[1]
        ax.plot(results_df.index, results_df['battery_soc'] * 100, 
                label='Battery SOC', color='green', linewidth=2)
        ax.set_ylabel('SOC (%)', fontsize=11)
        ax.set_title('Battery State of Charge', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 100])
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Plot 3: Grid Import/Export
        ax = axes[2]
        ax.plot(results_df.index, results_df['grid_import'], 
                label='Grid Import', color='red', linewidth=2)
        ax.plot(results_df.index, results_df['grid_export'], 
                label='Grid Export', color='blue', linewidth=2)
        ax.plot(results_df.index, results_df['net_grid'], 
                label='Net Grid (Import-Export)', color='purple', 
                linewidth=2, linestyle='--')
        ax.set_ylabel('Energy (kWh)', fontsize=11)
        ax.set_title('Grid Import/Export', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Plot 4: Energy Flow Distribution
        ax = axes[3]
        ax.plot(results_df.index, results_df['pv_to_load'], 
                label='PV to Load', color='orange', linewidth=1.5, alpha=0.7)
        ax.plot(results_df.index, results_df['pv_to_battery'], 
                label='PV to Battery', color='green', linewidth=1.5, alpha=0.7)
        ax.plot(results_df.index, results_df['battery_to_load'], 
                label='Battery to Load', color='darkgreen', linewidth=1.5, alpha=0.7)
        ax.set_ylabel('Energy (kWh)', fontsize=11)
        ax.set_title('Energy Flow Distribution', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Plot 5: Self-Sufficiency Rate
        ax = axes[4]
        ax.plot(results_df.index, results_df['self_sufficiency'] * 100, 
                label='Self-Sufficiency', color='darkblue', linewidth=2)
        ax.set_ylabel('Self-Sufficiency (%)', fontsize=11)
        ax.set_xlabel('Time', fontsize=11)
        ax.set_title('Self-Sufficiency Rate', fontsize=12, fontweight='bold')
        ax.set_ylim([0, 100])
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # Mark grid instability periods in all plots
        if 'grid_stable' in results_df.columns:
            for ax in axes:
                unstable_periods = results_df[~results_df['grid_stable']]
                if len(unstable_periods) > 0:
                    for idx in unstable_periods.index:
                        ax.axvspan(idx, idx, alpha=0.1, color='red')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        
        return fig


def load_input_data(irradiation_file: str, load_file: str, 
                    grid_stability_file: str) -> pd.DataFrame:
    """
    Load input data from CSV files.
    
    Args:
        irradiation_file: Path to solar irradiation CSV
        load_file: Path to load consumption CSV
        grid_stability_file: Path to grid stability CSV
        
    Returns:
        Combined DataFrame with all input data
    """
    irradiation_df = pd.read_csv(irradiation_file)
    load_df = pd.read_csv(load_file)
    grid_df = pd.read_csv(grid_stability_file)
    
    # Combine data
    data = pd.DataFrame({
        'irradiation_w_m2': irradiation_df['irradiation_w_m2'],
        'load_kw': load_df['load_kw'],
        'grid_stable': grid_df['grid_stable'].astype(bool)
    })
    
    return data


if __name__ == "__main__":
    # Example usage
    print("Energy System Simulation Module")
    print("Import this module to use the EnergySystem class")
