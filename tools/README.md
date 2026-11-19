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

## RGM-001E.11 Dataset Audit

See [Dataset Audit & Ground-Truth Evaluation](../docs/analysis/RGM-001E.11-DATASET-AUDIT.md).

```bash
python tools/rgm_dataset_audit.py dataset/ --seed 20261119 --output dataset_audit.json --split-manifest dataset_split_manifest.json
```
The audit validates captures, groups same-session and exact-duplicate evidence, quarantines unknown labels and assigns whole groups to train/calibration/evaluation. Observed labels remain unverified annotations; the readiness flag is structural only.

## RGM-001E.12 Verified Ground-Truth Evaluation

See [Verified Ground-Truth Evaluation](../docs/analysis/RGM-001E.12-GROUND-TRUTH-EVALUATION.md).

```bash
python tools/rgm_ground_truth_evaluator.py dataset_split_manifest.json verified_room_annotations.json scene_correlation.json --output ground_truth_evaluation.json
```
Only annotations with `verified=true`, reviewer and evidence are accepted. The threshold is calibrated on calibration pairs and applied to holdout evaluation pairs; cross-split pairs and unverified annotations are excluded.

## RGM-001E.13 Real Gameplay Collection

See [Real Gameplay Dataset Collection](../docs/analysis/RGM-001E.13-REAL-GAMEPLAY-COLLECTION.md).

```bash
python tools/rgm_experiment_plan.py --matrix docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json --output dataset/SESSION-0001 --session-id SESSION-0001
python tools/rgm_collection_status.py dataset/SESSION-0001 --output dataset/SESSION-0001/collection_status.json
```
The plan generator creates blank metadata templates only. The status auditor reports planned/captured/validated/invalid states and requires recorded artifact checksums before calling a capture validated. It does not infer ground-truth room identity.

## RGM-001E.14 Strict Ingestion Review

See [Ingestion Quality Review](../docs/analysis/RGM-001E.14-INGESTION-QUALITY-REVIEW.md).

```bash
python tools/rgm_ingestion_review.py dataset/SESSION-0001 --output dataset/SESSION-0001/ingestion_review.json
```
Checks each planned capture against session/experiment/checkpoint/repeat identity, the strict paired capture validator, full SHA-256 coverage and unexpected capture folders. It is read-only and does not verify ground-truth room identity.

## RGM-001E.15 Temporal Consistency

See [Temporal Consistency Protocol](../docs/analysis/RGM-001E.15-TEMPORAL-CONSISTENCY.md).

```bash
python tools/rgm_temporal_consistency.py dataset/SESSION-0001 --max-gap-ms 250 --output dataset/SESSION-0001/temporal_review.json
```
Requires optional monotonic timing metadata and, for a full pass, matching trusted game-frame markers. Timestamp proximity alone is not treated as proof of same-state capture.

## RGM-001E.15 Temporal Consistency

See [Temporal Consistency Protocol](../docs/analysis/RGM-001E.15-TEMPORAL-CONSISTENCY.md).

```bash
python tools/rgm_temporal_consistency.py dataset/SESSION-0001 --max-gap-ms 250 --output dataset/SESSION-0001/temporal_review.json
```
Requires monotonic-clock timing metadata and, for a full pass, matching trusted game-frame markers. Timestamp proximity alone is not proof of a frozen game state.

## RGM-001E.16 Capture Bundle Finalizer

The runtime adapter is staged under `integration/regaiden-recomp/`; see [integration guide](../docs/analysis/RGM-001E.16-RUNTIME-CAPTURE-ADAPTER.md). Once the adapter is integrated into a locally built upstream runtime and a real capture is produced, finalize its SHA-256 evidence:

```bash
python tools/rgm_capture_finalize.py dataset/SESSION-0001/FP-EXP-01-CP-01-R01
```
The finalizer hashes the state binary, state summary and all graphics dump files without modifying raw artifacts.

## RGM-001E.17 Upstream Integration

From the StarlightGaiden repository root, apply the guarded integration to the audited upstream checkout:

```bash
python integration/regaiden-recomp/apply_rgm_adapter.py ../regaiden-recomp
cmake -S ../regaiden-recomp -B ../regaiden-recomp/build -DCMAKE_BUILD_TYPE=Release
cmake --build ../regaiden-recomp/build --config Release --parallel
```

The script checks the upstream HEAD before editing and adds an opt-in one-shot capture CLI. See [RGM-001E.16 integration guide](../docs/analysis/RGM-001E.16-RUNTIME-CAPTURE-ADAPTER.md). Build and runtime testing remain pending.
