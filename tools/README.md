# RGM Snapshot Analyzer

Python 3 standard-library tool for inspecting the upstream `REGAIDEN-SNAPSHOT-1` binary snapshot format.

## Usage

Compare two memory snapshots:

```bash
python tools/rgm_snapshot_analyzer.py state_01.bin state_02.bin \
  --summary-a state_01.txt --summary-b state_02.txt \
  --output comparison.json
```

Inspect a single graphics capture:

```bash
python tools/rgm_snapshot_analyzer.py state_01.bin \
  --graphics-a path/to/capture_0001 --output inspection.json
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Current limits

- Memory blocks are WRAM, HRAM, IO and OAM only. VRAM/PPU are in the separate graphics dump.
- PNG inspection validates the PNG signature/IHDR metadata and computes SHA-256; it does not compare decoded pixels.
- No room, scene, active-character or speaker identity is inferred.
- Synthetic tests do not replace validation against captures from the actual game.
