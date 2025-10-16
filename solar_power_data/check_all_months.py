import pandas as pd
from pathlib import Path

# Get all monthly folders
base_dir = Path(__file__).parent
monthly_folders = sorted([f for f in base_dir.iterdir() if f.is_dir() and f.name.endswith("_solar")])

print("="*80)
print("CHECKING DATE RANGES IN ALL MONTHLY FOLDERS")
print("="*80)

results = []

for month_folder in monthly_folders:
    csv_files = list(month_folder.glob("*.csv"))
    
    if not csv_files:
        print(f"\n{month_folder.name}: No CSV files found")
        continue
    
    # Process the first CSV file in each folder
    csv_file = csv_files[0]
    
    try:
        df = pd.read_csv(csv_file)
        
        if 'interval_start_local' not in df.columns:
            print(f"\n{month_folder.name}: No 'interval_start_local' column")
            continue
        
        df['interval_start_local'] = pd.to_datetime(df['interval_start_local'])
        
        # Get unique intervals
        unique_intervals = sorted(df['interval_start_local'].unique())
        
        first_date = pd.to_datetime(unique_intervals[0])
        last_date = pd.to_datetime(unique_intervals[-1])
        days_covered = (last_date - first_date).days + 1
        unique_hours = len(unique_intervals)
        total_rows = len(df)
        duplicates_per_hour = total_rows / unique_hours if unique_hours > 0 else 0
        
        results.append({
            'month': month_folder.name,
            'file': csv_file.name,
            'first_date': first_date,
            'last_date': last_date,
            'days_covered': days_covered,
            'unique_hours': unique_hours,
            'total_rows': total_rows,
            'avg_duplicates': duplicates_per_hour
        })
        
        print(f"\n{month_folder.name}:")
        print(f"  File: {csv_file.name}")
        print(f"  Total rows: {total_rows:,}")
        print(f"  Unique hours: {unique_hours}")
        print(f"  Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
        print(f"  Days covered: {days_covered}")
        print(f"  Avg duplicates per hour: {duplicates_per_hour:.1f}")
        
    except Exception as e:
        print(f"\n{month_folder.name}: ERROR - {str(e)}")

# Summary table
print("\n" + "="*80)
print("SUMMARY TABLE")
print("="*80)
print(f"\n{'Month':<25} {'First Date':<12} {'Last Date':<12} {'Days':<6} {'Hours':<7}")
print("-"*80)

for r in results:
    print(f"{r['month']:<25} {r['first_date'].strftime('%Y-%m-%d'):<12} {r['last_date'].strftime('%Y-%m-%d'):<12} {r['days_covered']:<6} {r['unique_hours']:<7}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

total_hours = sum(r['unique_hours'] for r in results)
total_days = sum(r['days_covered'] for r in results)

print(f"\nTotal unique hours across all months: {total_hours}")
print(f"Total days covered across all months: {total_days}")
print(f"Average days per month: {total_days / len(results):.1f}")

# Check if any month has full data
full_months = [r for r in results if r['days_covered'] >= 28]
partial_months = [r for r in results if r['days_covered'] < 28]

print(f"\nMonths with full data (≥28 days): {len(full_months)}")
print(f"Months with partial data (<28 days): {len(partial_months)}")

if partial_months:
    print("\nPartial months:")
    for r in partial_months:
        print(f"  - {r['month']}: Only {r['days_covered']} days")
