"""
Main simulation script for the energy system.
"""

import argparse
from pathlib import Path
import pandas as pd
import yaml
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from energy_system import EnergySystem, load_input_data
from generate_input_data import generate_sample_data


def hours_to_dates(num_hours, start_date='2024-01-01'):
    """
    Convert hour indices to datetime objects for plotting.
    
    Args:
        num_hours: Number of hours
        start_date: Start date as string (YYYY-MM-DD)
        
    Returns:
        List of datetime objects
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    return [start + timedelta(hours=i) for i in range(num_hours)]


def plot_cumulative_energy(results: pd.DataFrame, save_path: str = None):
    """
    Plot cumulative energy flows over time.
    
    Args:
        results: DataFrame with simulation results
        save_path: Path to save the plot (optional)
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Convert hours to dates
    dates = hours_to_dates(len(results))
    
    # Calculate cumulative values
    cumulative_pv = results['pv_generation_kwh'].cumsum()
    cumulative_grid_import = results['grid_import'].cumsum()
    cumulative_grid_export = results['grid_export'].cumsum()
    cumulative_load = results['load_kwh'].cumsum()
    
    # Plot 1: Cumulative Energy Flows
    ax1.plot(dates, cumulative_pv, label='Total PV Generation', linewidth=2, color='orange')
    ax1.plot(dates, cumulative_load, label='Total Load Consumption', linewidth=2, color='blue')
    ax1.plot(dates, cumulative_grid_import, label='Total Grid Import', linewidth=2, color='red')
    ax1.plot(dates, cumulative_grid_export, label='Total Grid Export', linewidth=2, color='green')
    ax1.set_xlabel('Time (Months)', fontsize=12)
    ax1.set_ylabel('Cumulative Energy (kWh)')
    ax1.set_title('Cumulative Energy Flows')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    ax1.xaxis.set_minor_locator(mdates.MonthLocator())
    
    # Plot 2: Net Grid Energy (Export - Import, positive = profit)
    net_grid = cumulative_grid_export - cumulative_grid_import
    ax2.plot(dates, net_grid, linewidth=2, color='purple')
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax2.fill_between(dates, net_grid, 0, 
                      where=(net_grid >= 0), color='green', alpha=0.3, label='Net Export (Profit)')
    ax2.fill_between(dates, net_grid, 0, 
                      where=(net_grid < 0), color='red', alpha=0.3, label='Net Import (Cost)')
    ax2.set_xlabel('Time (Months)', fontsize=12)
    ax2.set_ylabel('Net Grid Energy (kWh)')
    ax2.set_title('Cumulative Net Grid Energy (Export - Import)')
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    ax2.xaxis.set_minor_locator(mdates.MonthLocator())
    
    plt.tight_layout()
    
    if save_path:
        from pathlib import Path
        base_path = Path(save_path).with_suffix('')
        
        # Export raw data
        plot_data = pd.DataFrame({
            'cumulative_pv': cumulative_pv,
            'cumulative_load': cumulative_load,
            'cumulative_grid_import': cumulative_grid_import,
            'cumulative_grid_export': cumulative_grid_export,
            'net_grid': net_grid
        })
        plot_data.to_csv(f"{base_path}_data.csv", index=True)
        print(f"Plot data saved to {base_path}_data.csv")
        
        # Save PNG and SVG
        plt.savefig(f"{base_path}.png", dpi=150, bbox_inches='tight')
        print(f"Plot saved to {base_path}.png")
        plt.savefig(f"{base_path}.svg", format='svg', bbox_inches='tight')
        print(f"Plot saved to {base_path}.svg")
        plt.close()
    else:
        plt.show()


def simulate_baseline_system(data: pd.DataFrame, grid_import_cost: float, 
                             diesel_cost_per_kwh: float = None):
    """
    Simulate a baseline system with only grid and diesel generator.
    
    Args:
        data: DataFrame with load_kw and grid_stable columns
        grid_import_cost: Cost per kWh from grid
        diesel_cost_per_kwh: Cost per kWh from diesel generator
        
    Returns:
        Dictionary with baseline system metrics
    """
    total_load = data['load_kw'].sum()
    
    # When grid is stable, use grid; when unstable, use diesel
    grid_available_load = data[data['grid_stable'] == True]['load_kw'].sum()
    diesel_load = data[data['grid_stable'] == False]['load_kw'].sum()
    
    # Calculate costs
    grid_cost = grid_available_load * grid_import_cost
    diesel_cost = diesel_load * diesel_cost_per_kwh if diesel_cost_per_kwh else 0
    total_cost = grid_cost + diesel_cost
    
    return {
        'total_load': total_load,
        'grid_energy': grid_available_load,
        'diesel_energy': diesel_load,
        'grid_cost': grid_cost,
        'diesel_cost': diesel_cost,
        'total_cost': total_cost
    }


def plot_cost_over_time(results: pd.DataFrame, data: pd.DataFrame, 
                       grid_import_cost: float, grid_export_price: float,
                       diesel_cost_per_kwh: float, save_path: str = None):
    """
    Plot cumulative costs over time for both systems.
    
    Args:
        results: DataFrame with solar system simulation results
        data: DataFrame with load and grid stability data
        grid_import_cost: Cost per kWh from grid
        grid_export_price: Price per kWh for grid export
        diesel_cost_per_kwh: Cost per kWh from diesel
        save_path: Path to save the plot (optional)
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    
    # Convert hours to dates
    dates = hours_to_dates(len(data))
    
    # Calculate baseline cumulative costs
    baseline_grid_cost = []
    baseline_diesel_cost = []
    for i in range(len(data)):
        if data.iloc[i]['grid_stable']:
            baseline_grid_cost.append(data.iloc[i]['load_kw'] * grid_import_cost)
            baseline_diesel_cost.append(0)
        else:
            baseline_grid_cost.append(0)
            baseline_diesel_cost.append(data.iloc[i]['load_kw'] * diesel_cost_per_kwh)
    
    cumulative_baseline = (pd.Series(baseline_grid_cost) + pd.Series(baseline_diesel_cost)).cumsum()
    
    # Calculate solar system cumulative costs (negative = profit)
    solar_import_costs = results['grid_import'] * grid_import_cost
    solar_export_revenue = results['grid_export'] * grid_export_price
    solar_net_cost = solar_import_costs - solar_export_revenue
    cumulative_solar = solar_net_cost.cumsum()
    
    # Plot both systems
    ax.plot(dates, cumulative_baseline, label='Baseline (Grid + Diesel)', linewidth=2.5, color='red', alpha=0.8)
    ax.plot(dates, cumulative_solar, label='Solar + Battery', linewidth=2.5, color='green', alpha=0.8)
    ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Fill area between curves to show savings
    ax.fill_between(dates, cumulative_baseline, cumulative_solar, 
                     alpha=0.2, color='gold', label='Savings Area')
    
    ax.set_xlabel('Time (Months)', fontsize=12)
    ax.set_ylabel('Cumulative Cost / Profit (€)', fontsize=12)
    ax.set_title('Cumulative Cost Comparison Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator())
    
    # Add final values as annotations
    final_baseline = cumulative_baseline.iloc[-1]
    final_solar = cumulative_solar.iloc[-1]
    ax.annotate(f'Final: €{final_baseline:,.0f}', 
                xy=(dates[-1], final_baseline), 
                xytext=(-80, -30), textcoords='offset points',
                fontsize=10, fontweight='bold', color='darkred',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='darkred'))
    
    profit_label = f'Final: €{final_solar:,.0f}\n(Profit!)' if final_solar < 0 else f'Final: €{final_solar:,.0f}'
    ax.annotate(profit_label, 
                xy=(dates[-1], final_solar), 
                xytext=(-80, 30), textcoords='offset points',
                fontsize=10, fontweight='bold', color='darkgreen',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='darkgreen'))
    
    plt.tight_layout()
    
    if save_path:
        from pathlib import Path
        base_path = Path(save_path).with_suffix('')
        
        # Export raw data
        plot_data = pd.DataFrame({
            'cumulative_baseline': cumulative_baseline,
            'cumulative_solar': cumulative_solar,
            'savings': cumulative_baseline - cumulative_solar
        })
        plot_data.to_csv(f"{base_path}_data.csv", index=True)
        print(f"Plot data saved to {base_path}_data.csv")
        
        # Save PNG and SVG
        plt.savefig(f"{base_path}.png", dpi=150, bbox_inches='tight')
        print(f"Plot saved to {base_path}.png")
        plt.savefig(f"{base_path}.svg", format='svg', bbox_inches='tight')
        print(f"Plot saved to {base_path}.svg")
        plt.close()
    else:
        plt.show()


def plot_co2_comparison(results: pd.DataFrame, data: pd.DataFrame,
                        co2_grid: float, co2_diesel: float, co2_pv: float,
                        save_path_prefix: str = None):
    """Plot CO2 emissions comparison: baseline vs solar+battery.

    - Baseline: grid (when available) + diesel (when grid down)
    - Solar+Battery: grid import emissions + PV lifecycle emissions
    """
    # Per-timestep CO2 (kg)
    baseline_co2 = []
    solar_co2 = []
    for i in range(len(data)):
        # Baseline
        if data.iloc[i]['grid_stable']:
            baseline_co2.append(data.iloc[i]['load_kw'] * co2_grid)
        else:
            baseline_co2.append(data.iloc[i]['load_kw'] * co2_diesel)

        # Solar+battery system: grid imports have grid emissions, PV generation has lifecycle emissions
        # For PV, count pv_generation_kwh * co2_pv as lifecycle overhead
        grid_import_kwh = results.iloc[i]['grid_import'] if 'grid_import' in results.columns else 0
        pv_kwh = results.iloc[i]['pv_generation_kwh'] if 'pv_generation_kwh' in results.columns else 0
        solar_co2.append(grid_import_kwh * co2_grid + pv_kwh * co2_pv)

    baseline_co2 = pd.Series(baseline_co2)
    solar_co2 = pd.Series(solar_co2)

    # Annual totals
    total_baseline_co2 = baseline_co2.sum()
    total_solar_co2 = solar_co2.sum()

    # Monthly aggregation for time series plot
    dates = hours_to_dates(len(data))
    df_co2 = pd.DataFrame({'date': dates, 'baseline_co2': baseline_co2, 'solar_co2': solar_co2})
    df_co2['month'] = [d.month for d in df_co2['date']]
    monthly = df_co2.groupby('month')[['baseline_co2', 'solar_co2']].sum().reset_index()
    # Compute monthly difference (baseline - solar)
    monthly['diff_co2_kg'] = monthly['baseline_co2'] - monthly['solar_co2']

    # Compute cumulative CO2 time series (starting at 0)
    cumulative_baseline_co2 = df_co2['baseline_co2'].cumsum()
    cumulative_solar_co2 = df_co2['solar_co2'].cumsum()

    # Plot 1: Annual bar comparison
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    systems = ['Baseline (Grid+Diesel)', 'Solar+Battery']
    values = [total_baseline_co2, total_solar_co2]
    bars = ax.bar(systems, values, color=['tab:red', 'tab:green'], alpha=0.8)
    ax.set_ylabel('Total CO2 (kg)')
    ax.set_title('Annual CO2 Emissions: Baseline vs Solar+Battery', fontsize=12, fontweight='bold')
    for i, v in enumerate(values):
        ax.text(i, v + max(values)*0.01, f'{v:,.0f} kg', ha='center', va='bottom')

    plt.tight_layout()
    if save_path_prefix:
        from pathlib import Path
        base = Path(save_path_prefix).with_suffix('')
        # export data
        pd.DataFrame({'system': systems, 'co2_kg': values}).to_csv(f'{base}_annual_co2.csv', index=False)
        plt.savefig(f'{base}_co2_annual.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{base}_co2_annual.svg', format='svg', bbox_inches='tight')
        plt.close()

        # --- Financial-style CO2 comparison (stacked breakdown + net annual bars) ---
        # Compute breakdowns
        # Baseline breakdown: grid vs diesel
        baseline_grid_co2 = df_co2[df_co2['date'].notna() & (data['grid_stable'].values == True)]['baseline_co2'].sum() if 'grid_stable' in data.columns else 0
        baseline_diesel_co2 = df_co2[df_co2['date'].notna() & (data['grid_stable'].values == False)]['baseline_co2'].sum() if 'grid_stable' in data.columns else 0

        # Solar system breakdown: grid import emissions and PV lifecycle emissions
        solar_grid_import_co2 = results['grid_import'].sum() * co2_grid if 'grid_import' in results.columns else 0
        solar_pv_co2 = results['pv_generation_kwh'].sum() * co2_pv if 'pv_generation_kwh' in results.columns else 0

        # Prepare CSV data for this comparison
        comp_df = pd.DataFrame({
            'component': ['baseline_grid_co2', 'baseline_diesel_co2', 'solar_grid_import_co2', 'solar_pv_co2'],
            'co2_kg': [baseline_grid_co2, baseline_diesel_co2, solar_grid_import_co2, solar_pv_co2]
        })
        comp_df.to_csv(f'{base}_co2_comparison_data.csv', index=False)

        # Plot two-panel comparison similar to financial chart
        fig, (ax1_co2, ax2_co2) = plt.subplots(1, 2, figsize=(16, 8))

        # Left: stacked breakdown
        systems_co2 = ['Baseline\n(Grid + Diesel)', 'Solar + Battery']
        # Baseline stacked
        ax1_co2.bar(0, baseline_grid_co2, label='Grid CO2', color='red', alpha=0.7)
        ax1_co2.bar(0, baseline_diesel_co2, bottom=baseline_grid_co2, label='Diesel CO2', color='orange', alpha=0.7)
        # Solar stacked
        ax1_co2.bar(1, solar_grid_import_co2, label='Grid Import CO2', color='salmon', alpha=0.7)
        ax1_co2.bar(1, solar_pv_co2, bottom=solar_grid_import_co2, label='PV Lifecycle CO2', color='lightgreen', alpha=0.7)

        ax1_co2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax1_co2.set_ylabel('CO2 Emissions (kg)', fontsize=12)
        ax1_co2.set_title('CO2 Breakdown Comparison', fontsize=14, fontweight='bold')
        ax1_co2.set_xticks([0, 1])
        ax1_co2.set_xticklabels(systems_co2, fontsize=11)
        ax1_co2.legend(loc='upper right')
        ax1_co2.grid(True, alpha=0.3, axis='y')

        # Add value labels
        baseline_total_co2 = baseline_grid_co2 + baseline_diesel_co2
        solar_total_co2 = solar_grid_import_co2 + solar_pv_co2
        ax1_co2.text(0, baseline_total_co2 + max(baseline_total_co2, solar_total_co2)*0.01, f'{baseline_total_co2:,.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold', color='darkred')
        ax1_co2.text(1, solar_total_co2 + max(baseline_total_co2, solar_total_co2)*0.01, f'{solar_total_co2:,.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold', color='darkgreen')

        # Right: Net annual CO2 bars
        net_values_co2 = [baseline_total_co2, solar_total_co2]
        colors_co2 = ['red' if v > 0 else 'green' for v in net_values_co2]
        bars_co2 = ax2_co2.bar(systems_co2, net_values_co2, color=colors_co2, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax2_co2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2_co2.set_ylabel('Net Annual CO2 (kg)', fontsize=12)
        ax2_co2.set_title('Net Annual CO2 Comparison', fontsize=14, fontweight='bold')
        ax2_co2.grid(True, alpha=0.3, axis='y')

        # Add labels on bars
        for i, (bar, value) in enumerate(zip(bars_co2, net_values_co2)):
            label_y = value + (max(net_values_co2) * 0.02)
            ax2_co2.text(i, label_y, f'{value:,.0f} kg', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # Add savings annotation (CO2 reduction)
        co2_savings = baseline_total_co2 - solar_total_co2
        reduction_pct = (co2_savings / baseline_total_co2 * 100) if baseline_total_co2 > 0 else 0
        ax2_co2.text(0.5, max(net_values_co2) * 0.6, f'CO2 Reduction:\n{co2_savings:,.0f} kg\n({reduction_pct:.1f}% reduction)', ha='center', va='center', fontsize=12, fontweight='bold', bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', alpha=0.7, edgecolor='black'))

        plt.tight_layout()
        plt.savefig(f'{base}_co2_comparison.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{base}_co2_comparison.svg', format='svg', bbox_inches='tight')
        plt.close()

    # Plot 2: Monthly time series
    fig, ax = plt.subplots(1, 1, figsize=(12, 5))
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    ax.plot(monthly['month'], monthly['baseline_co2'], label='Baseline CO2', color='red', marker='o')
    ax.plot(monthly['month'], monthly['solar_co2'], label='Solar+Battery CO2', color='green', marker='o')
    ax.set_xticks(range(1,13))
    ax.set_xticklabels(months)
    ax.set_ylabel('Monthly CO2 (kg)')
    ax.set_title('Monthly CO2 Emissions by System', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path_prefix:
        pd.DataFrame(monthly).to_csv(f'{base}_monthly_co2.csv', index=False)
        plt.savefig(f'{base}_co2_monthly.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{base}_co2_monthly.svg', format='svg', bbox_inches='tight')
        plt.close()

        # Plot 3: Monthly CO2 difference (Baseline - Solar)
        fig, ax = plt.subplots(1, 1, figsize=(12, 5))
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        ax.bar(monthly['month'], monthly['diff_co2_kg'], color='tab:blue', alpha=0.8)
        ax.set_xticks(range(1,13))
        ax.set_xticklabels(months)
        ax.set_ylabel('Monthly CO2 Difference (kg)')
        ax.set_title('Monthly CO2 Reduction (Baseline - Solar+Battery)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        # Annotate bars with values
        for idx, val in enumerate(monthly['diff_co2_kg']):
            ax.text(monthly['month'].iloc[idx], val + max(monthly['diff_co2_kg']) * 0.01, f'{val:,.0f}',
                    ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        # export monthly diff data and plots
        monthly.to_csv(f'{base}_monthly_co2_diff.csv', index=False)
        plt.savefig(f'{base}_co2_monthly_diff.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{base}_co2_monthly_diff.svg', format='svg', bbox_inches='tight')
        plt.close()

    # Plot 4: Cumulative CO2 line chart (starts at 0) to compare which system consumed more over time
    fig, ax = plt.subplots(1, 1, figsize=(14, 6))
    dates_full = df_co2['date']
    ax.plot(dates_full, cumulative_baseline_co2, label='Baseline (Cumulative CO2)', color='red', linewidth=2)
    ax.plot(dates_full, cumulative_solar_co2, label='Solar+Battery (Cumulative CO2)', color='green', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Cumulative CO2 (kg)')
    ax.set_title('Cumulative CO2 Emissions Over Time (Baseline vs Solar+Battery)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    # Save underlying CSV (per-timestep cumulative values)
    cum_df = pd.DataFrame({'date': dates_full, 'cumulative_baseline_co2_kg': cumulative_baseline_co2, 'cumulative_solar_co2_kg': cumulative_solar_co2})
    cum_df.to_csv(f'{base}_co2_cumulative.csv', index=False)
    plt.tight_layout()
    plt.savefig(f'{base}_co2_cumulative.png', dpi=150, bbox_inches='tight')
    plt.savefig(f'{base}_co2_cumulative.svg', format='svg', bbox_inches='tight')
    plt.close()

    return {
        'total_baseline_co2_kg': total_baseline_co2,
        'total_solar_co2_kg': total_solar_co2,
        'monthly': monthly
    }


def plot_winter_soc_selfsufficiency(results: pd.DataFrame, start_date: datetime, winter_months: list, save_path_prefix: str = None):
    """Plot battery SOC and self-sufficiency for the configured winter months.

    Args:
        results: simulation results DataFrame (must contain 'battery_soc' and 'self_sufficiency')
        start_date: datetime corresponding to index 0 in results
        winter_months: list of month numbers (1-12) to include
        save_path_prefix: path prefix (string) to save outputs, e.g. 'output/co2_comparison'

    Produces PNG, SVG and CSV of filtered time series.
    """
    if not winter_months:
        print("No winter months configured, skipping winter SOC/self-sufficiency plot.")
        return None

    # build dates for index
    dates = hours_to_dates(len(results), start_date=start_date.strftime('%Y-%m-%d') if start_date else '2024-01-01')
    df = results.copy().reset_index(drop=True)
    df['date'] = dates
    df['month'] = [d.month for d in df['date']]

    # filter to winter months
    winter_df = df[df['month'].isin(winter_months)].copy().reset_index(drop=True)
    if winter_df.empty:
        print("Winter months selection contains no data; skipping winter plot.")
        return None

    # Handle ordering so we can plot from a chosen start month (support overflow across year boundary)
    # Choose start month: prefer December (12) if present, otherwise the smallest configured month
    start_month = 12 if 12 in winter_months else min(winter_months)
    # Create an order key that wraps months after start_month
    winter_df['order_key'] = winter_df['month'].apply(lambda m: (m - start_month) % 12)
    # Sort by order_key then by actual date to keep hourly order within each month
    winter_df = winter_df.sort_values(['order_key', 'date']).reset_index(drop=True)

    # Prepare series as percentages
    winter_df['battery_soc_pct'] = winter_df['battery_soc'] * 100
    winter_df['self_sufficiency_pct'] = winter_df['self_sufficiency'] * 100

    # Create plot indices so Dec..Jan appear contiguous (overflow)
    winter_df['plot_index'] = range(len(winter_df))

    # Find month boundaries for xticks and labels
    month_starts = winter_df.groupby(['month', 'order_key'])['plot_index'].first().reset_index()
    # Map month number to short name
    month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                   7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

    # Plot two stacked subplots: battery SOC on top, self-sufficiency below
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.plot(winter_df['plot_index'], winter_df['battery_soc_pct'], label='Battery SOC (%)', color='tab:green', linewidth=1.5)
    ax1.set_ylabel('Battery SOC (%)')
    ax1.set_ylim(0, 100)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')

    ax2.plot(winter_df['plot_index'], winter_df['self_sufficiency_pct'], label='Self-sufficiency (%)', color='tab:blue', linewidth=1.5)
    ax2.set_ylabel('Self-sufficiency (%)')
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left')

    # X ticks at month starts with labels like 'Dec' and 'Jan'
    xticks = month_starts['plot_index'].tolist()
    xlabels = [f"{month_names.get(m, str(m))}" for m in month_starts['month'].tolist()]
    ax2.set_xticks(xticks)
    ax2.set_xticklabels(xlabels)

    # Add small title and a combined xlabel
    fig.suptitle('Winter Window: Battery SOC and Self-sufficiency (Dec → Jan overflow)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Month')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save outputs
    if save_path_prefix:
        from pathlib import Path
        base = Path(save_path_prefix).with_suffix('')
        # CSV includes original date for reference plus plot_index ordering
        winter_df[['date', 'month', 'plot_index', 'battery_soc_pct', 'self_sufficiency_pct']].to_csv(f'{base}_winter_soc_selfsufficiency_data.csv', index=False)
        plt.savefig(f'{base}_winter_soc_selfsufficiency.png', dpi=150, bbox_inches='tight')
        plt.savefig(f'{base}_winter_soc_selfsufficiency.svg', format='svg', bbox_inches='tight')
        plt.close()
        print(f"Winter SOC/self-sufficiency plot and data saved with prefix: {base}_winter_soc_selfsufficiency.*")
        return f'{base}_winter_soc_selfsufficiency'
    else:
        plt.show()
        return None


def plot_cost_comparison(baseline_costs: dict, solar_import_cost: float, 
                        solar_export_revenue: float, save_path: str = None):
    """
    Create a graphical comparison of costs between baseline and solar+battery systems.
    
    Args:
        baseline_costs: Dictionary with baseline system costs
        solar_import_cost: Cost for grid import in solar system
        solar_export_revenue: Revenue from grid export in solar system
        save_path: Path to save the plot (optional)
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Cost Breakdown Comparison
    systems = ['Baseline\n(Grid + Diesel)', 'Solar + Battery']
    
    # Baseline costs (positive = cost)
    baseline_grid = baseline_costs['grid_cost']
    baseline_diesel = baseline_costs['diesel_cost']
    baseline_total = baseline_costs['total_cost']
    
    # Solar system (positive = cost, negative = revenue)
    solar_net = solar_import_cost - solar_export_revenue
    
    # Create stacked bar for baseline
    ax1.bar(0, baseline_grid, label='Grid Cost', color='red', alpha=0.7)
    ax1.bar(0, baseline_diesel, bottom=baseline_grid, label='Diesel Cost', color='orange', alpha=0.7)
    
    # Create bar for solar system
    if solar_net >= 0:
        # Net cost
        ax1.bar(1, solar_import_cost, label='Grid Import Cost', color='salmon', alpha=0.7)
        ax1.bar(1, -solar_export_revenue, bottom=solar_import_cost, label='Grid Export Revenue', color='lightgreen', alpha=0.7)
    else:
        # Net profit
        ax1.bar(1, solar_import_cost, label='Grid Import Cost', color='salmon', alpha=0.7)
        ax1.bar(1, -solar_export_revenue, bottom=solar_import_cost, label='Grid Export Revenue', color='lightgreen', alpha=0.7)
    
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_ylabel('Cost / Revenue (€)', fontsize=12)
    ax1.set_title('Cost Breakdown Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(systems, fontsize=11)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    ax1.text(0, baseline_total + 50000, f'€{baseline_total:,.0f}', 
             ha='center', va='bottom', fontsize=11, fontweight='bold', color='darkred')
    ax1.text(1, solar_net - 50000 if solar_net < 0 else solar_net + 50000, 
             f'€{solar_net:,.0f}', ha='center', 
             va='top' if solar_net < 0 else 'bottom', 
             fontsize=11, fontweight='bold', 
             color='darkgreen' if solar_net < 0 else 'darkred')
    
    # Plot 2: Net Cost/Profit Comparison (simplified)
    net_values = [baseline_total, solar_net]
    colors = ['red' if v > 0 else 'green' for v in net_values]
    bars = ax2.bar(systems, net_values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_ylabel('Net Annual Cost / Profit (€)', fontsize=12)
    ax2.set_title('Net Annual Financial Comparison', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, net_values)):
        label_y = value + (50000 if value > 0 else -50000)
        va = 'bottom' if value > 0 else 'top'
        label_text = f'Cost: €{value:,.0f}' if value > 0 else f'Profit: €{abs(value):,.0f}'
        ax2.text(i, label_y, label_text, ha='center', va=va, 
                fontsize=11, fontweight='bold')
    
    # Add savings annotation
    savings = baseline_total - solar_net
    ax2.text(0.5, max(net_values) * 0.5, 
             f'💰 Total Savings:\n€{savings:,.0f}\n({(savings/baseline_total)*100:.1f}% reduction)',
             ha='center', va='center', fontsize=13, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.8', facecolor='yellow', alpha=0.7, edgecolor='black'))
    
    plt.tight_layout()
    
    if save_path:
        from pathlib import Path
        base_path = Path(save_path).with_suffix('')
        
        # Export raw data
        plot_data = pd.DataFrame({
            'system': systems,
            'baseline_grid_cost': [baseline_grid, 0],
            'baseline_diesel_cost': [baseline_diesel, 0],
            'solar_import_cost': [0, solar_import_cost],
            'solar_export_revenue': [0, solar_export_revenue],
            'net_cost': net_values
        })
        plot_data.to_csv(f"{base_path}_data.csv", index=False)
        print(f"Plot data saved to {base_path}_data.csv")
        
        # Save PNG and SVG
        plt.savefig(f"{base_path}.png", dpi=150, bbox_inches='tight')
        print(f"Plot saved to {base_path}.png")
        plt.savefig(f"{base_path}.svg", format='svg', bbox_inches='tight')
        print(f"Plot saved to {base_path}.svg")
        plt.close()
    else:
        plt.show()


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
    
    # Note: output directory will be created after config values are applied
    

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
        # Cost parameters
        grid_import_cost = config.get('grid_import_cost', None)
        grid_export_price = config.get('grid_export_price', None)
        diesel_cost_per_kwh = config.get('diesel_cost_per_kwh', None)
        # Seasonal battery management
        winter_months = config.get('winter_months', [])
        winter_min_soc = config.get('winter_min_soc', 0.0)
        outage_min_soc = config.get('outage_min_soc', 0.0)
        # CO2 emission factors
        co2_grid = config.get('co2_grid_kg_per_kwh', 0.4)
        co2_diesel = config.get('co2_diesel_kg_per_kwh', 0.8)
        co2_pv = config.get('co2_pv_kg_per_kwh', 0.05)
    else:
        target_pv_peak_kw = None
        target_annual_load_kwh = None
        solar_scale_factor = 1.0
        load_scale_factor = 1.0
        start_date = None
        end_date = None
        grid_import_cost = None
        grid_export_price = None
        diesel_cost_per_kwh = None
        winter_months = []
        winter_min_soc = 0.0
        outage_min_soc = 0.0
        co2_grid = 0.4
        co2_diesel = 0.8
        co2_pv = 0.05
    # After applying config overrides, create the output directory so config.output_dir is respected
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
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
    if winter_months and winter_min_soc > 0:
        print(f"  Winter reserve: {winter_min_soc * 100}% SOC in months {winter_months}")
    if outage_min_soc is not None:
        print(f"  Outage reserve minimum SOC: {outage_min_soc * 100}% (allowed during outages)")
    
    system = EnergySystem(
        pv_peak_kw=pv_peak_kw,
        battery_capacity_kwh=battery_capacity_kwh,
        battery_efficiency=battery_efficiency,
        battery_self_discharge=battery_self_discharge,
        winter_months=winter_months,
        winter_min_soc=winter_min_soc,
        outage_min_soc=outage_min_soc
    )
    
    # Run simulation
    print("\nRunning simulation...")
    # Convert start_date string to datetime if provided
    sim_start_date = None
    if start_date:
        try:
            sim_start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except:
            sim_start_date = datetime(2024, 1, 1)
    
    results = system.simulate(data, timestep_hours=timestep_hours, start_date=sim_start_date)
    
    # Annotate blackout periods (when load is not fully served)
    results['blackout'] = results['unmet_load'] > 0
    
    # Detect contiguous blackout events and export details
    blackout_events = []
    in_event = False
    event_start = None
    for i, is_blackout in enumerate(results['blackout'].values):
        if is_blackout and not in_event:
            in_event = True
            event_start = i
        elif not is_blackout and in_event:
            # event ends at i-1
            event_end = i - 1
            event_slice = results.iloc[event_start:event_end+1]
            duration = event_end - event_start + 1
            unserved = float(event_slice['unmet_load'].sum())
            min_soc = float((event_slice['battery_soc'] * 100).min()) if 'battery_soc' in event_slice else None
            avg_soc = float((event_slice['battery_soc'] * 100).mean()) if 'battery_soc' in event_slice else None
            grid_down_ratio = float((~event_slice['grid_stable']).mean()) if 'grid_stable' in event_slice else None
            # timestamps
            if sim_start_date is None:
                sim_start_date = datetime(2024, 1, 1)
            start_ts = sim_start_date + timedelta(hours=event_start)
            end_ts = sim_start_date + timedelta(hours=event_end)
            blackout_events.append({
                'event_id': len(blackout_events) + 1,
                'start_index': event_start,
                'end_index': event_end,
                'start_time': start_ts,
                'end_time': end_ts,
                'duration_hours': duration,
                'unserved_energy_kwh': unserved,
                'min_battery_soc_pct': min_soc,
                'avg_battery_soc_pct': avg_soc,
                'grid_down_fraction': grid_down_ratio
            })
            in_event = False
            event_start = None
    # If still in event at the end
    if in_event and event_start is not None:
        event_end = len(results) - 1
        event_slice = results.iloc[event_start:event_end+1]
        duration = event_end - event_start + 1
        unserved = float(event_slice['unmet_load'].sum())
        min_soc = float((event_slice['battery_soc'] * 100).min()) if 'battery_soc' in event_slice else None
        avg_soc = float((event_slice['battery_soc'] * 100).mean()) if 'battery_soc' in event_slice else None
        grid_down_ratio = float((~event_slice['grid_stable']).mean()) if 'grid_stable' in event_slice else None
        if sim_start_date is None:
            sim_start_date = datetime(2024, 1, 1)
        start_ts = sim_start_date + timedelta(hours=event_start)
        end_ts = sim_start_date + timedelta(hours=event_end)
        blackout_events.append({
            'event_id': len(blackout_events) + 1,
            'start_index': event_start,
            'end_index': event_end,
            'start_time': start_ts,
            'end_time': end_ts,
            'duration_hours': duration,
            'unserved_energy_kwh': unserved,
            'min_battery_soc_pct': min_soc,
            'avg_battery_soc_pct': avg_soc,
            'grid_down_fraction': grid_down_ratio
        })
    
    # Save results
    results_file = output_path / "simulation_results.csv"
    results.to_csv(results_file)
    print(f"\nResults saved to: {results_file}")
    
    # Export blackout events if any
    if blackout_events:
        be_df = pd.DataFrame(blackout_events)
        be_df.to_csv(output_path / 'blackout_events.csv', index=False)
        total_blackout_hours = int(results['blackout'].sum())
        total_events = len(be_df)
        worst = int(be_df['duration_hours'].max())
        total_unserved = float(be_df['unserved_energy_kwh'].sum())
        print(f"\n--- Resilience Summary (Blackouts) ---")
        print(f"Blackout events: {total_events}")
        print(f"Total blackout hours: {total_blackout_hours}")
        print(f"Longest blackout: {worst} hours")
        print(f"Total unserved energy: {total_unserved:.2f} kWh")
        print(f"Details saved to: {output_path / 'blackout_events.csv'}")
    else:
        print(f"\n--- Resilience Summary (Blackouts) ---")
        print(f"No blackout events. All load served across the period.")
    
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

    # Prepare annual summary dictionary
    annual_summary = {
        'total_pv_generation_kwh': float(total_pv_generation),
        'total_load_kwh': float(total_load),
        'total_grid_import_kwh': float(total_grid_import),
        'total_grid_export_kwh': float(total_grid_export),
        'net_grid_energy_kwh': float(total_grid_import - total_grid_export),
        'avg_self_sufficiency_pct': float(avg_self_sufficiency * 100),
        'total_unmet_load_kwh': float(total_unmet_load)
    }

    # Add financials if available
    if 'import_cost' in locals():
        annual_summary['grid_import_cost_eur'] = float(import_cost)
    if 'export_revenue' in locals():
        annual_summary['grid_export_revenue_eur'] = float(export_revenue)
    if 'net_balance' in locals():
        annual_summary['net_electricity_balance_eur'] = float(net_balance)

    # Add CO2 totals if CO2 computation ran
    try:
        if 'co2_res' in locals():
            annual_summary['co2_baseline_kg'] = float(co2_res.get('total_baseline_co2_kg', 0.0))
            annual_summary['co2_solar_kg'] = float(co2_res.get('total_solar_co2_kg', 0.0))
    except Exception:
        # ignore if co2_res unavailable
        pass

    # Write annual summary CSV
    try:
        summary_df = pd.DataFrame([annual_summary])
        summary_file = output_path / 'annual_summary.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"\nAnnual summary saved to: {summary_file}")
    except Exception as e:
        print(f"Failed to write annual summary CSV: {e}")
    
    # Calculate costs if specified
    if grid_import_cost is not None or grid_export_price is not None:
        print("\n" + "-" * 60)
        print("Financial Summary")
        print("-" * 60)
        if grid_import_cost is not None:
            import_cost = total_grid_import * grid_import_cost
            print(f"Grid import cost: €{import_cost:,.2f} (@ €{grid_import_cost}/kWh)")
        if grid_export_price is not None:
            export_revenue = total_grid_export * grid_export_price
            print(f"Grid export revenue: €{export_revenue:,.2f} (@ €{grid_export_price}/kWh)")
        if grid_import_cost is not None and grid_export_price is not None:
            net_balance = export_revenue - import_cost
            print(f"\nNet electricity balance: €{net_balance:,.2f}")
            if net_balance > 0:
                print(f"  → Net profit: €{net_balance:,.2f} (You earned money!)")
            else:
                print(f"  → Net cost: €{abs(net_balance):,.2f} (You paid this amount)")

    
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
    
    # Create cumulative energy flow plot
    print("Generating cumulative energy flow plot...")
    cumulative_plot_file = output_path / "cumulative_energy_flows.png"
    plot_cumulative_energy(results, save_path=str(cumulative_plot_file))
    print(f"Cumulative energy plot saved to: {cumulative_plot_file}")

    # Create winter months SOC/self-sufficiency plot
    try:
        winter_plot_prefix = str(output_path / 'co2_comparison')
        # use sim_start_date (datetime) for date construction if available
        plot_winter_soc_selfsufficiency(results, sim_start_date if sim_start_date else datetime(2024,1,1), winter_months, save_path_prefix=winter_plot_prefix)
    except Exception as e:
        print(f"Failed to create winter SOC/self-sufficiency plot: {e}")
    
    # Compare with baseline system (grid + diesel)
    if grid_import_cost is not None:
        print("\n" + "=" * 60)
        print("Baseline System Comparison (Grid + Diesel Generator)")
        print("=" * 60)
        
        baseline = simulate_baseline_system(data, grid_import_cost, diesel_cost_per_kwh)
        
        print(f"\nBaseline System (No Solar/Battery):")
        print(f"  Grid energy: {baseline['grid_energy']:,.2f} kWh")
        print(f"  Diesel energy: {baseline['diesel_energy']:,.2f} kWh")
        print(f"  Grid cost: €{baseline['grid_cost']:,.2f}")
        if diesel_cost_per_kwh:
            print(f"  Diesel cost: €{baseline['diesel_cost']:,.2f}")
        print(f"  Total cost: €{baseline['total_cost']:,.2f}")
        
        print(f"\nSolar + Battery System:")
        if grid_import_cost is not None and grid_export_price is not None:
            solar_system_cost = import_cost - export_revenue
            print(f"  Net cost: €{-solar_system_cost:,.2f}")
            
            savings = baseline['total_cost'] - (-solar_system_cost)
            print(f"\n💰 Total Savings: €{savings:,.2f}")
            if baseline['total_cost'] > 0:
                savings_pct = (savings / baseline['total_cost']) * 100
                print(f"   Cost Reduction: {savings_pct:.1f}%")
            
            # Create cost comparison plot
            print("\nGenerating cost comparison chart...")
            comparison_plot_file = output_path / "cost_comparison.png"
            plot_cost_comparison(baseline, import_cost, export_revenue, 
                               save_path=str(comparison_plot_file))
            print(f"Cost comparison chart saved to: {comparison_plot_file}")
            
            # Create cost over time plot
            print("Generating cost over time chart...")
            cost_time_plot_file = output_path / "cost_over_time.png"
            plot_cost_over_time(results, data, grid_import_cost, grid_export_price,
                              diesel_cost_per_kwh, save_path=str(cost_time_plot_file))
            print(f"Cost over time chart saved to: {cost_time_plot_file}")
            # CO2 comparison
            print("\nGenerating CO2 emissions comparison plots...")
            co2_prefix = str(output_path / 'co2_comparison')
            co2_res = plot_co2_comparison(results, data, co2_grid, co2_diesel, co2_pv, save_path_prefix=co2_prefix)
            print(f"CO2 annual - Baseline: {co2_res['total_baseline_co2_kg']:.0f} kg, Solar: {co2_res['total_solar_co2_kg']:.0f} kg")
            print(f"CO2 plots and data saved with prefix: {co2_prefix}")
    
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
