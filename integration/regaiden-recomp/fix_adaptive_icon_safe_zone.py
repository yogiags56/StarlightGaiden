#!/usr/bin/env python3
"""Scale adaptive icon foreground layers into Android's launcher safe zone."""
from pathlib import Path
from PIL import Image
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: fix_adaptive_icon_safe_zone.py <android-res-dir>")
res = Path(sys.argv[1])
assets = res / "drawable-nodpi"
# Android launchers apply a mask to the central portion of an adaptive icon.
# Keep the complete Gaiden wordmark comfortably inside that mask.
SCALE = 0.62
for name in ("ic_launcher_foreground.png", "ic_launcher_monochrome.png"):
    path = assets / name
    image = Image.open(path).convert("RGBA")
    if image.width != image.height:
        raise SystemExit(f"{path}: expected a square adaptive-icon layer")
    w, h = image.size
    scaled = image.resize((round(w * SCALE), round(h * SCALE)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((w - scaled.width) // 2, (h - scaled.height) // 2))
    canvas.save(path)
    print(f"Safe-zone adjusted: {path}")
