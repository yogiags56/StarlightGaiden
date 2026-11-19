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
| RGM-001E.11 | Dataset Audit & Ground-Truth Evaluation | Deterministic session-grouped split planner, exact duplicate audit and quarantine rules implemented; real labels/captures still outstanding |
| RGM-001E.12 | Verified Ground-Truth Evaluation | Human-verified annotation schema, calibration-only threshold selection and holdout evaluator implemented; real evaluation pending |
| RGM-001E.13 | Real Gameplay Dataset Collection | Collection status auditor and capture workflow documented; waiting for actual paired gameplay dumps |
| RGM-001E.14 | Real Capture Ingestion & Quality Review | Read-only plan identity, artifact/checksum coverage and unexpected-folder reviewer implemented; waiting for real dumps |
| RGM-001E.15 | Capture Synchronization & Temporal Consistency | Timing/frame evidence auditor and synthetic tests implemented; runtime instrumentation and real paired captures pending |
| RGM-001E.15 | Capture Synchronization & Temporal Consistency | Timing/frame evidence auditor and synthetic tests implemented; runtime instrumentation and real paired captures still pending |
| RGM-001E.16 | Runtime Capture Bundle Adapter | C++ adapter, checksum finalizer and integration instructions staged |
| RGM-001E.17 | Guarded Upstream Integration & Build Verification | Exact-commit integration script, opt-in CLI hook, transactional anchor checks and fixture tests implemented |\n| RGM-001E.18 | Desktop Adapter Smoke Verification | Full upstream desktop CMake build and executable verification passed in CI; no-ROM startup/CLI smoke test newly added and awaiting CI; real gameplay/capture pending |
| RGM-002 | Upstream build and compatibility | Not started |
| RGM-003 | Gameplay verification | Not started |
| RGM-004 | Asset pipeline | Not started |
| RGM-005 | Exploration presentation | Not started |
| RGM-006 | Combat presentation | Not started |
| RGM-007 | UI and controls | Not started |
| RGM-008 | Audio and optimization | Not started |
| RGM-009 | Regression and release | Not started |

## Immediate sequence

1. Clone `sergiomanzur/regaiden-recomp` at audited commit `e5befd20e67939d939319149d1c1177b8e6c5cd6`.
2. Apply `python integration/regaiden-recomp/apply_rgm_adapter.py ../regaiden-recomp` from the StarlightGaiden repository root.
3. Configure and build the complete upstream desktop target with CMake.
4. Run without RGM options and verify ordinary gameplay remains unchanged.
5. Run one opt-in capture with a legally obtained local ROM and operator-confirmed labels.
6. Finalize SHA-256 values and run capture ingestion/temporal reviewers.
7. Proceed to Android ARM64 only after desktop build and capture gates pass.

## Earlier analysis sequence

1. Capture paired memory and graphics snapshots from the same game state.
2. Run the dataset integrity validator and repair missing metadata/checksums.
3. Collect repeated same-room captures with stationary, movement and camera-scroll conditions.
4. Collect different-room negative controls with visually similar corridors/walls.
5. Measure false positives/negatives and calibrate thresholds.
6. Only then consider a verified room identity layer and scene/character classifiers.
