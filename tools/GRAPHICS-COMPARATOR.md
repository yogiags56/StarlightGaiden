# RGM Graphics Comparator

Python 3 standard-library tool for the PNG files emitted by upstream `asset_dump.c`.

## Run

```bash
python tools/rgm_graphics_comparator.py dataset/SESSION-0001/FP-001/capture_0001 dataset/SESSION-0001/FP-002/capture_0001 --output graphics_diff.json
```

The tool compares:
- `map_9800.png` and `map_9c00.png` as 32×32 grids of 8×8-pixel cells.
- `framebuffer.png` pixel-by-pixel, including a changed-pixel bounding box.
- Matching `tiles_*.png` sheets pixel-by-pixel.

The decoder intentionally supports the upstream dumper's 8-bit RGBA, non-interlaced PNG format. It validates PNG chunk CRCs and implements PNG filters 0–4. No Pillow dependency is required.

## Interpretation limits

Tilemap PNGs are rendered images with CGB palette, bank and flip attributes already applied. The comparator does not recover original tile indices, raw VRAM bytes or attributes. Palette animation, tile animation and graphics streaming can cause visual differences without a room change. The tool therefore reports differences only; it does not assign room IDs, scene IDs, character identities or speaker identities.
