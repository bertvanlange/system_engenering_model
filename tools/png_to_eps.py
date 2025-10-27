from PIL import Image
from pathlib import Path
import sys

def convert(png_path, eps_path=None):
    p = Path(png_path)
    if not p.exists():
        print(f"Input not found: {p}")
        return 2
    if eps_path is None:
        eps_path = p.with_suffix('.eps')
    try:
        im = Image.open(p)
        # Convert to RGB to avoid palette/mode issues
        if im.mode != 'RGB':
            im = im.convert('RGB')
        im.save(eps_path, format='EPS')
        print(f"Converted: {p} -> {eps_path}")
        return 0
    except Exception as e:
        print(f"Conversion failed: {e}")
        return 3

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python tools\\png_to_eps.py <input_png> [output_eps]")
        sys.exit(1)
    png = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(convert(png, out))
