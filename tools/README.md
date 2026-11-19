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

## Multi-Signal Scene Correlation

See [MULTI-SIGNAL-CORRELATION.md](MULTI-SIGNAL-CORRELATION.md) for map, memory, runtime, camera, sprite and audio evidence correlation.

```bash
python tools/rgm_scene_correlator.py dataset/ --output scene_correlation.json
```

## Scene State Classification Foundation

See [SCENE-STATE-CLASSIFICATION.md](SCENE-STATE-CLASSIFICATION.md) for conservative UI-family and dialogue-geometry evidence rules.

```bash
python tools/rgm_scene_classifier.py dataset/ --output scene_states.json
```

## Controlled Gameplay Experiment Plan

See [RGM-001E.9-CONTROLLED-EXPERIMENTS.md](../docs/analysis/RGM-001E.9-CONTROLLED-EXPERIMENTS.md) and the [experiment matrix](../docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json).

```bash
python tools/rgm_experiment_plan.py --output dataset/SESSION-0001 --session-id SESSION-0001
```
The generator creates empty metadata templates only. It does not capture or invent game data.

## RGM-001E.10 Real Gameplay Capture Ingestion

See [real capture ingestion specification](../docs/analysis/RGM-001E.10-REAL-CAPTURE-INGESTION.md). The generator writes `FP-<capture_id>` folders that are discovered by the validator. The validator rejects missing real snapshots/graphics, mismatched session/capture IDs, unsafe paths and checksum mismatches.
