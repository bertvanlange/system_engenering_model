# Quick Start Guide - Energy System Simulation

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Option 1: Generate sample data and run simulation
```bash
python simulate.py --generate-sample-data
```

This will:
- Generate 7 days of sample input data
- Run the simulation with default parameters
- Save results to `output/simulation_results.csv`
- Create visualization in `output/simulation_results.png`

### Option 2: Run with custom parameters
```bash
python simulate.py \
  --pv-peak 150 \
  --battery-capacity 300 \
  --battery-efficiency 0.95 \
  --generate-sample-data \
  --days 14
```

## Input Data Format

The simulation requires three CSV files:

### 1. solar_irradiation.csv
Solar irradiation in W/m²
```csv
hour,irradiation_w_m2
0,0.0
1,0.0
2,0.0
6,30.5
12,850.0
18,100.0
```

### 2. load_consumption.csv
Load power demand in kW
```csv
hour,load_kw
0,50.5
1,48.2
2,52.1
6,90.3
12,75.8
```

### 3. grid_stability.csv
Grid availability status
```csv
hour,grid_stable
0,True
1,True
2,False
3,True
```

## Parameters

### System Configuration
- `--pv-peak`: PV system peak power in kW (default: 100.0)
- `--battery-capacity`: Battery capacity in kWh (default: 200.0)
- `--battery-efficiency`: Battery charge/discharge efficiency 0-1 (default: 0.95)
- `--battery-self-discharge`: Self-discharge rate per timestep (default: 0.0001)
- `--timestep`: Time step duration in hours (default: 1.0)

### Input/Output
- `--irradiation`: Path to solar irradiation CSV
- `--load`: Path to load consumption CSV
- `--grid`: Path to grid stability CSV
- `--output-dir`: Output directory (default: output)

### Data Generation
- `--generate-sample-data`: Generate sample input data
- `--days`: Number of days for sample data (default: 7)

## Examples

### Example 1: High PV capacity system
```bash
python simulate.py \
  --pv-peak 200 \
  --battery-capacity 300 \
  --generate-sample-data
```

### Example 2: Run example scenarios
```bash
python examples.py
```

This will run multiple scenarios:
- High PV capacity (150 kW)
- Large battery (400 kWh)
- Unstable grid (50% stability)
- System configuration comparison

## Output

### simulation_results.csv
Contains detailed timestep data:
- `pv_generation_kwh`: PV energy generated
- `load_kwh`: Load energy demand
- `battery_soc`: Battery state of charge (0-1)
- `battery_energy_kwh`: Battery energy content
- `pv_to_load`: Energy flow from PV to load
- `pv_to_battery`: Energy flow from PV to battery
- `battery_to_load`: Energy flow from battery to load
- `grid_to_load`: Energy import from grid
- `grid_import`: Total grid import
- `grid_export`: Total grid export
- `net_grid`: Net grid energy (import - export)
- `self_sufficiency`: Self-sufficiency ratio (0-1)
- `unmet_load`: Unmet load during grid outage

### simulation_results.png
Visualization with 5 plots:
1. PV Generation and Load
2. Battery State of Charge
3. Grid Import/Export
4. Energy Flow Distribution
5. Self-Sufficiency Rate

## Testing

Run the test suite:
```bash
python test_energy_system.py
```

This verifies:
- Battery charge/discharge functionality
- PV power generation
- Complete energy system simulation
- Energy flow priority logic

## Python API

Use the simulation programmatically:

```python
from energy_system import EnergySystem, load_input_data

# Load data
data = load_input_data(
    'input_data/solar_irradiation.csv',
    'input_data/load_consumption.csv',
    'input_data/grid_stability.csv'
)

# Create system
system = EnergySystem(
    pv_peak_kw=100.0,
    battery_capacity_kwh=200.0,
    battery_efficiency=0.95
)

# Run simulation
results = system.simulate(data, timestep_hours=1.0)

# Create plots
system.plot_results(results, save_path='output/results.png')

# Analyze results
print(f"Average self-sufficiency: {results['self_sufficiency'].mean():.2%}")
print(f"Total grid import: {results['grid_import'].sum():.2f} kWh")
print(f"Total grid export: {results['grid_export'].sum():.2f} kWh")
```

## Energy Flow Priority

The simulation follows this priority order:

1. **PV → Load**: Solar panels feed the load first
2. **PV excess → Battery**: Excess PV energy charges the battery
3. **Battery → Load**: Battery supplements if PV is insufficient
4. **Grid → Load**: Grid imports when PV + Battery cannot meet demand
5. **PV/Battery excess → Grid**: Excess energy exports to grid

## Key Metrics

- **Self-Sufficiency Rate**: Percentage of load met by local generation (PV + Battery)
- **Grid Import/Export**: Energy exchanged with the grid
- **Battery Cycles**: Number of charge/discharge cycles
- **Unmet Load**: Load not satisfied during grid outages

## Troubleshooting

### Issue: Missing input files
**Solution**: Use `--generate-sample-data` to create sample input files

### Issue: Import errors
**Solution**: Install dependencies: `pip install -r requirements.txt`

### Issue: Plots not displaying
**Solution**: Check that matplotlib is installed and output directory is writable

## Tips

1. **Optimize system size**: Use `examples.py` to compare different configurations
2. **Model validation**: Run `test_energy_system.py` to verify functionality
3. **Custom scenarios**: Modify input CSV files to test specific conditions
4. **Long simulations**: Increase `--days` parameter for longer time periods
5. **Grid resilience**: Adjust grid stability to model different scenarios
