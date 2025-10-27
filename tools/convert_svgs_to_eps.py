"""
Convert all SVG files in the repository (or provided paths) to EPS using cairosvg.
Saves .eps side-by-side with the original .svg and does NOT overwrite existing .eps unless --overwrite is used.

Usage (from repo root):
    python tools\convert_svgs_to_eps.py --root . --overwrite False

"""
import argparse
from pathlib import Path
import sys

try:
    import cairosvg
except Exception as e:
    print("cairosvg is required. Please install via pip: pip install cairosvg")
    raise


def convert_file(svg_path: Path, overwrite: bool = False):
    eps_path = svg_path.with_suffix('.eps')
    if eps_path.exists() and not overwrite:
        print(f"Skipping existing: {eps_path}")
        return False
    try:
        cairosvg.svg2eps(url=str(svg_path), write_to=str(eps_path))
        print(f"Converted: {svg_path} -> {eps_path}")
        return True
    except Exception as e:
        print(f"Failed to convert {svg_path}: {e}")
        return False


def find_svgs(root: Path, include_patterns=None):
    if include_patterns:
        svgs = []
        for pat in include_patterns:
            svgs.extend(list(root.glob(pat)))
        return sorted(set(svgs))
    else:
        return sorted(root.rglob('*.svg'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str, default='.', help='Repository root to search for SVG files')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing .eps files')
    parser.add_argument('--only', type=str, default=None, help='Optional glob (relative to root) to limit which SVGs to convert, e.g. "output/*.svg"')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.only:
        patterns = [args.only]
    else:
        patterns = None

    svgs = find_svgs(root, include_patterns=patterns)
    if not svgs:
        print(f"No SVG files found under: {root}")
        return 0

    converted = []
    skipped = []
    failed = []
    for s in svgs:
        ok = convert_file(s, overwrite=args.overwrite)
        if ok:
            converted.append(s.with_suffix('.eps'))
        else:
            # if eps exists we treat as skipped
            if s.with_suffix('.eps').exists():
                skipped.append(s.with_suffix('.eps'))
            else:
                failed.append(s)

    print('\nConversion summary:')
    print(f'  converted: {len(converted)}')
    print(f'  skipped (existing eps): {len(skipped)}')
    print(f'  failed: {len(failed)}')
    if converted:
        for c in converted:
            print(f'    {c}')

    return 0

if __name__ == '__main__':
    sys.exit(main())
