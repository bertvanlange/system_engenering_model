"""
Simple test script to verify the energy system simulation.
"""

import pandas as pd
import numpy as np
from energy_system import Battery, PVSystem, EnergySystem


def test_battery():
    """Test battery charge/discharge functionality."""
    print("Testing Battery...")
    battery = Battery(capacity_kwh=100, efficiency=0.95, initial_soc=0.5)
    
    # Test initial state
    assert battery.get_soc() == 0.5, "Initial SOC should be 0.5"
    assert battery.energy_kwh == 50.0, "Initial energy should be 50 kWh"
    
    # Test charging
    charged = battery.charge(20.0)
    assert charged > 0, "Should be able to charge"
    assert battery.get_soc() > 0.5, "SOC should increase after charging"
    
    # Test discharging
    soc_before = battery.get_soc()
    discharged = battery.discharge(10.0)
    assert discharged > 0, "Should be able to discharge"
    assert battery.get_soc() < soc_before, "SOC should decrease after discharging"
    
    # Test self-discharge
    energy_before = battery.energy_kwh
    battery.apply_self_discharge(1.0)
    assert battery.energy_kwh < energy_before, "Energy should decrease after self-discharge"
    
    print("✓ Battery tests passed")


def test_pv_system():
    """Test PV system power generation."""
    print("Testing PV System...")
    pv = PVSystem(peak_power_kw=100)
    
    # Test at peak irradiation
    power = pv.generate_power(1000)
    assert power == 100.0, "Should generate peak power at 1000 W/m²"
    
    # Test at half irradiation
    power = pv.generate_power(500)
    assert power == 50.0, "Should generate half power at 500 W/m²"
    
    # Test at zero irradiation
    power = pv.generate_power(0)
    assert power == 0.0, "Should generate zero power at 0 W/m²"
    
    print("✓ PV System tests passed")


def test_energy_system():
    """Test complete energy system simulation."""
    print("Testing Energy System...")
    system = EnergySystem(pv_peak_kw=100, battery_capacity_kwh=200)
    
    # Create simple test data
    test_data = pd.DataFrame({
        'irradiation_w_m2': [1000, 500, 0, 800],
        'load_kw': [50, 60, 40, 70],
        'grid_stable': [True, True, False, True]
    })
    
    # Run simulation
    results = system.simulate(test_data, timestep_hours=1.0)
    
    # Verify results structure
    assert len(results) == 4, "Should have 4 timesteps"
    assert 'pv_generation_kwh' in results.columns, "Should have PV generation"
    assert 'load_kwh' in results.columns, "Should have load"
    assert 'battery_soc' in results.columns, "Should have battery SOC"
    assert 'grid_import' in results.columns, "Should have grid import"
    assert 'self_sufficiency' in results.columns, "Should have self-sufficiency"
    
    # Verify energy balance (within tolerance for battery efficiency)
    for idx, row in results.iterrows():
        # Total energy to load should match load demand (or be less if unmet)
        total_to_load = row['pv_to_load'] + row['battery_to_load'] + row['grid_to_load']
        total_demand = row['load_kwh']
        unmet = row['unmet_load']
        # Allow small tolerance for battery efficiency and rounding
        assert abs(total_to_load + unmet - total_demand) < 0.1, f"Energy balance error at timestep {idx}: supply={total_to_load}, demand={total_demand}, unmet={unmet}"
    
    # Verify self-sufficiency is in valid range
    assert all(results['self_sufficiency'] >= 0), "Self-sufficiency should be >= 0"
    assert all(results['self_sufficiency'] <= 1), "Self-sufficiency should be <= 1"
    
    # Verify battery SOC is in valid range
    assert all(results['battery_soc'] >= 0), "Battery SOC should be >= 0"
    assert all(results['battery_soc'] <= 1), "Battery SOC should be <= 1"
    
    print("✓ Energy System tests passed")


def test_energy_flow_priority():
    """Test that energy flows in correct priority."""
    print("Testing Energy Flow Priority...")
    system = EnergySystem(pv_peak_kw=100, battery_capacity_kwh=200)
    
    # Test case 1: PV exactly meets load
    result = system.simulate_timestep(
        irradiation_w_m2=500,  # Generates 50 kW
        load_kw=50,
        grid_stable=True,
        timestep_hours=1.0
    )
    assert result['pv_to_load'] == 50, "PV should feed load first"
    assert result['grid_import'] == 0, "Should not import from grid"
    assert result['self_sufficiency'] == 1.0, "Should be 100% self-sufficient"
    
    # Test case 2: PV exceeds load
    result = system.simulate_timestep(
        irradiation_w_m2=1000,  # Generates 100 kW
        load_kw=60,
        grid_stable=True,
        timestep_hours=1.0
    )
    assert result['pv_to_load'] == 60, "PV should feed load first"
    assert result['pv_to_battery'] > 0, "Excess PV should charge battery"
    
    # Test case 3: PV insufficient, battery provides
    result = system.simulate_timestep(
        irradiation_w_m2=200,  # Generates 20 kW
        load_kw=50,
        grid_stable=True,
        timestep_hours=1.0
    )
    assert result['pv_to_load'] == 20, "All PV should go to load"
    assert result['battery_to_load'] > 0, "Battery should provide remaining load"
    
    print("✓ Energy Flow Priority tests passed")


if __name__ == "__main__":
    print("=" * 60)
    print("Running Energy System Tests")
    print("=" * 60)
    print()
    
    try:
        test_battery()
        test_pv_system()
        test_energy_system()
        test_energy_flow_priority()
        
        print()
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise
