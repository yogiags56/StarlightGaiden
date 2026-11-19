# Development Roadmap

Status reflects work actually completed in this repository, not estimates.

| Milestone | Scope | Status |
|---|---|---|
| RGM-001A/B | Upstream source, gameplay and asset reconnaissance | Design/audit notes carried forward; no local build |
| RGM-001C | Gameplay state and renderer audit | Audit complete; unresolved detection heuristics documented |
| RGM-001D | Character state and scene mapping | Audit complete; active character/speaker still unverified |
| RGM-001E.1 | Fingerprint specification | Specification complete |
| RGM-001E.2 | Snapshot dataset and capture protocol | Protocol drafted; no actual game dataset collected |
| RGM-001E.3 | Snapshot Analyzer | Prototype integrated; synthetic tests to be run in this repository |
| RGM-001E.4 | Graphics and tilemap comparator | Next |
| RGM-002 | Upstream build and compatibility | Not started |
| RGM-003 | Gameplay verification | Not started |
| RGM-004 | Asset pipeline | Not started |
| RGM-005 | Exploration presentation | Not started |
| RGM-006 | Combat presentation | Not started |
| RGM-007 | UI and controls | Not started |
| RGM-008 | Audio and optimization | Not started |
| RGM-009 | Regression and release | Not started |

## Immediate sequence

1. Validate the snapshot parser using synthetic fixtures and malformed inputs.
2. Integrate graphics pixel/tilemap comparison without treating palette animation as room identity.
3. Capture paired memory and graphics snapshots from the same game state.
4. Derive room/scene/character signals only from repeatable comparisons.
5. Audit and replace unverified runtime heuristics only after evidence and tests exist.
