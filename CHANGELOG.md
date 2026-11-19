# Changelog

## Unreleased — RGM-001E.5 Room Fingerprint Engine

- Added per-cell rendered RGBA tile hashes for 32×32 tilemap captures.
- Added a translation-invariant tile-pattern multiset digest (coarse descriptor).
- Added circular tilemap offset search and inverse-frequency weighted similarity.
- Added optional evidence-based excluded-cell masks and overlap gates.
- Added a minimum pattern-diversity gate to reject ambiguous repetitive maps.
- Added explicit candidate/weak/insufficient states; no automatic room identity assignment.
- Added synthetic tests for exact match, camera/ring-buffer offset recovery and low-overlap/low-diversity rejection.

## RGM-001E.4 Graphics Comparator

- Added a standard-library RGBA PNG decoder for upstream asset-dump output.
- Added pixel-level framebuffer and tile-sheet comparison.
- Added 32×32 tilemap cell comparison and 4-way contiguous change regions.
- Added CRC checks, malformed PNG validation and synthetic comparator tests.
- Explicitly documents that visual tilemap diffs are not raw VRAM tile-index comparisons and cannot independently identify rooms.

## RGM-001E.3 repository bootstrap

- Initialized the StarlightGaiden project repository.
- Added project direction, roadmap, architecture/provenance and snapshot protocol.
- Integrated the offline snapshot analyzer prototype.
- Added synthetic unit tests; real game data and Android runtime validation remain pending.

## Unreleased — RGM-001E.6 Capture Validation Harness

- Added paired state/graphics capture metadata and file-integrity validator.
- Added path traversal protection for metadata file references.
- Added snapshot structure, PNG dimension and required-file checks.
- Added pairwise fingerprint trials grouped by tester-entered location labels.
- Added synthetic tests for valid captures, checksum mismatch and path traversal.
- Real-game captures and ground-truth validation remain pending.

## Unreleased — RGM-001E.7 Multi-Signal Scene Correlation

- Added pairwise correlation across both rendered tilemaps, WRAM/HRAM/IO/OAM deltas, ROM/WRAM banks, PC, LCD/camera registers, active sprites and music-track hint.
- Parses the actual upstream state_dump.c text-summary layout.
- Reads the music-track hint from WRAM offset 0x0E8C, matching the inspected upstream helper.
- Emits candidate/weak/insufficient evidence only; no room, scene, active-character or speaker identity is assigned.
- Added synthetic tests for summary parsing and pairwise correlation; real-game calibration remains pending.

## Unreleased — RGM-001E.8 Scene State Classification Foundation

- Added a conservative per-capture evidence classifier for the eight target scene categories.
- Reports the WRAM bank-2 UI family without pretending to distinguish inventory, PDA, title and save menus.
- Reports a dialogue candidate only from the upstream LCDC/WX/WY geometry heuristic and non-UI bank context.
- Leaves exploration, cutscene, normal/boss combat, room transition, save/load, active character and speaker unresolved pending real captures.
- Added synthetic tests for UI-family handling, dialogue geometry and unknown fallback.

## Unreleased — RGM-001E.9 Controlled Gameplay Capture Experiments

- Added an 11-experiment matrix covering exploration, inventory/item detail, PDA/menu, dialogue, ordinary combat, boss combat, room transition, cutscene, save/load, character identity controls and look-alike-room negative controls.
- Added a blank session-plan generator that creates capture metadata templates only; it does not fabricate state snapshots or graphics.
- Added tests for template generation, duplicate experiment IDs and path-traversal rejection in session IDs.
- Added a controlled capture protocol and acceptance gates. Real gameplay captures remain outstanding.

## Unreleased — RGM-001E.10 Real Gameplay Capture Ingestion

- Fixed the capture-plan generator to emit FP-prefixed directories consumed by the dataset validator.
- Strengthened validation of capture ID/session directory consistency, required state summaries, and non-empty graphics manifests.
- Added integration coverage proving generated blank plans are discovered and rejected as incomplete until actual game data is supplied.
- Added the real capture ingestion specification. No gameplay captures were fabricated or claimed.

## Unreleased — RGM-001E.11 Dataset Audit & Ground-Truth Evaluation

- Added deterministic SHA-256 evidence inventory and exact duplicate grouping.
- Added leakage-resistant split assignment by connected session/duplicate groups.
- Added train/calibration/evaluation splits and quarantine for unknown labels.
- Added dataset audit report and reproducible split manifest output.
- Added synthetic tests for session leakage, exact duplicate grouping, deterministic assignment, unknown-label quarantine and invalid ratios.
- No real-game dataset or ground-truth accuracy results are claimed.

## Unreleased — RGM-001E.12 Verified Ground-Truth Evaluation

- Added explicit human-verified room annotation schema requiring reviewer and evidence notes.
- Added calibration-only threshold selection using balanced accuracy, with F1 and higher-threshold tie-breaks.
- Added independent holdout evaluation with confusion counts and standard classification metrics.
- Cross-split and unverified-label pairs are excluded; calibration requires both same-room and different-room examples.
- Added synthetic tests for calibration/holdout separation, unverified annotations, missing classes and annotation provenance.
- No real-game labels or performance results are claimed.
