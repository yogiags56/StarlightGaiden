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
| RGM-001E.6 | Real Capture Validation Harness | Implemented; synthetic integrity/pairwise tests pending CI; awaiting real captures |
| RGM-002 | Upstream build and compatibility | Not started |
| RGM-003 | Gameplay verification | Not started |
| RGM-004 | Asset pipeline | Not started |
| RGM-005 | Exploration presentation | Not started |
| RGM-006 | Combat presentation | Not started |
| RGM-007 | UI and controls | Not started |
| RGM-008 | Audio and optimization | Not started |
| RGM-009 | Regression and release | Not started |

## Immediate sequence

1. Capture paired memory and graphics snapshots from the same game state.
2. Run the dataset integrity validator and repair missing metadata/checksums.
3. Collect repeated same-room captures with stationary, movement and camera-scroll conditions.
4. Collect different-room negative controls with visually similar corridors/walls.
5. Measure false positives/negatives and calibrate thresholds.
6. Only then consider a verified room identity layer and scene/character classifiers.
