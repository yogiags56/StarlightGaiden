# Development Roadmap

Status reflects work actually completed in this repository, not estimates.

| Milestone | Scope | Status |
|---|---|---|
| RGM-001A/B | Upstream source, gameplay and asset reconnaissance | Audit notes carried forward; no local build |
| RGM-001C | Gameplay state and renderer audit | Audit complete; unresolved detection heuristics documented |
| RGM-001D | Character state and scene mapping | Audit complete; active character/speaker still unverified |
| RGM-001E.1 | Fingerprint specification | Complete |
| RGM-001E.2 | Snapshot dataset and capture protocol | Protocol drafted; no real dataset collected |
| RGM-001E.3 | Snapshot Analyzer | Integrated; synthetic tests pass |
| RGM-001E.4 | Graphics and tilemap comparator | Implemented; synthetic tests pass |
| RGM-001E.5 | Room Fingerprint Engine | Experimental candidate matcher; synthetic tests pass; not calibrated on real captures |
| RGM-001E.6 | Real Capture Validation Harness | Implemented; synthetic integrity/pairwise tests pass; awaiting real captures |
| RGM-001E.7 | Multi-Signal Scene Correlation | Implemented; synthetic parser/correlation tests pass; awaiting real captures |
| RGM-001E.8 | Scene State Classification Foundation | Implemented; synthetic evidence and unknown-fallback tests pass; awaiting real captures |
| RGM-001E.9 | Controlled Gameplay Capture Experiments | Protocol, 11-experiment matrix and blank-plan generator implemented; awaiting actual game captures |
| RGM-001E.10 | Real Gameplay Capture Ingestion | Canonical folder layout and strict metadata/integrity validation implemented; real captures still outstanding |
| RGM-001E.11 | Dataset Audit & Ground-Truth Evaluation | Deterministic session-grouped split planner, exact duplicate audit and quarantine rules implemented; real labels/captures still outstanding |\n| RGM-001E.12 | Verified Ground-Truth Evaluation | Human-verified annotation schema, calibration-only threshold selection and holdout evaluator implemented; real evaluation pending |
| RGM-002 | Upstream build and compatibility | Not started |
| RGM-003 | Gameplay verification | Not started |
| RGM-004 | Asset pipeline | Not started |
| RGM-005 | Exploration presentation | Not started |
| RGM-006 | Combat presentation | Not started |
| RGM-007 | UI and controls | Not started |
| RGM-008 | Audio and optimization | Not started |
| RGM-009 | Regression and release | Not started |

## Immediate sequence

1. Generate a session plan with `python tools/rgm_experiment_plan.py --output dataset/SESSION-0001 --session-id SESSION-0001`.
2. Populate generated FP capture folders with actual paired dumps; run the capture validator.
3. Execute reachable experiments in `docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json` and capture paired state/graphics dumps.
4. Validate captures and preserve originals/checksums.
5. Evaluate same-room positive controls and visually similar different-room negative controls.
6. Run dataset audit and preserve its split manifest with the dataset version.
7. Add human-reviewed room annotations with evidence notes.\n8. Calibrate on the calibration split and evaluate once on the independent holdout split; do not tune against evaluation results.

## Earlier analysis sequence

1. Capture paired memory and graphics snapshots from the same game state.
2. Run the dataset integrity validator and repair missing metadata/checksums.
3. Collect repeated same-room captures with stationary, movement and camera-scroll conditions.
4. Collect different-room negative controls with visually similar corridors/walls.
5. Measure false positives/negatives and calibrate thresholds.
6. Only then consider a verified room identity layer and scene/character classifiers.
