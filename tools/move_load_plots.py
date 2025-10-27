import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "Dataset on Hourly Load Profiles for 24 Facilities (8760 hours) pciturs"
if not target.exists():
    print(f"Target folder does not exist: {target}")
    raise SystemExit(1)

# collect basenames from dataset CSVs
csv_folder = root / "Dataset on Hourly Load Profiles for 24 Facilities (8760 hours)"
basenames = [p.stem for p in csv_folder.glob('*.csv')]
print(f"Found {len(basenames)} dataset basenames to consider.")

moved = []
skipped = []
for stem in basenames:
    for ext in ('.png', '.svg', '.eps'):
        src = root / (stem + ext)
        dst = target / (stem + ext)
        if src.exists():
            if dst.exists():
                skipped.append(str(dst))
                print(f"Skipping (exists): {dst}")
            else:
                try:
                    shutil.move(str(src), str(dst))
                    moved.append(str(dst))
                    print(f"Moved: {src} -> {dst}")
                except Exception as e:
                    print(f"Failed to move {src}: {e}")

print('\nSummary:')
print(f'  moved: {len(moved)}')
print(f'  skipped (already present): {len(skipped)}')
if moved:
    for p in moved:
        print('    ' + p)
