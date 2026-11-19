# Development Roadmap

Status reflects work actually completed in this repository, not estimates.

| Milestone | Scope | Status |
|---|---|---|
| RGM-001A/B | Upstream source, gameplay and asset reconnaissance | Design/audit notes carried forward; no local build |
| RGM-001C | Gameplay state and renderer audit | Audit complete; unresolved detection heuristics documented |
| RGM-001D | Character state and scene mapping | Audit complete; active character/speaker still unverified |
| RGM-001E.1 | Fingerprint specification | Specification complete |
| RGM-001E.2 | Snapshot dataset and capture protocol | Protocol drafted; no actual game dataset collected |
| RGM-001E.3 | Snapshot Analyzer | Integrated; synthetic tests pass |
| RGM-001E.4 | Graphics and tilemap comparator | Implemented; CI passes; awaiting real game captures |
| RGM-001E.5 | Room Fingerprint Engine | Experimental candidate matcher implemented; synthetic tests pass; not calibrated on real captures |
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
2. Establish repeatability for stationary, camera-scroll, animation and palette variation.
3. Evaluate false positives with negative-control rooms.
4. Calibrate overlap, diversity and similarity thresholds on a labeled dataset.
5. Only then design scene-state and active-character classification.
