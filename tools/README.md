# RGM Analysis Tools

## Snapshot Analyzer

See [rgm_snapshot_analyzer.py](rgm_snapshot_analyzer.py) for parsing and comparing WRAM, HRAM, IO and OAM snapshots.

## Graphics Comparator

See [GRAPHICS-COMPARATOR.md](GRAPHICS-COMPARATOR.md) for usage and limitations.

Run all tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Room Fingerprint Engine

See [ROOM-FINGERPRINT.md](ROOM-FINGERPRINT.md) for the experimental 32×32 tilemap fingerprint and camera/ring-buffer offset matcher.

Run its tests with:

```bash
python -m unittest tests.test_room_fingerprint -v
```

## Real Capture Validation

See [REAL-CAPTURE-VALIDATION.md](REAL-CAPTURE-VALIDATION.md) for paired capture integrity checks and labeled fingerprint trials.

```bash
python tools/rgm_capture_validator.py dataset/ --output dataset_validation.json
```
