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
- Corrected the single-class calibration fixture to exercise the intended insufficient-class guard.
- No real-game labels or performance results are claimed.

## Unreleased — RGM-001E.13 Real Gameplay Dataset Collection

- Added a read-only collection progress auditor for planned, captured, validated and invalid checkpoints.
- Added capture/session identity and path traversal checks to the collection status report.
- Require recorded source SHA-256 metadata before a capture is marked validated.
- Added synthetic tests for blank plans, validated paired dumps, incomplete captures, path traversal and session identity mismatch.
- Documented the 11-experiment/45-checkpoint/3-repeat capture workflow and provenance requirements.
- No real gameplay capture data is included or claimed.

## Unreleased — RGM-001E.14 Real Capture Ingestion & Dataset Quality Review

- Added read-only session ingestion review against planned capture identity.
- Validates capture/session/experiment/checkpoint/repeat fields, strict paired artifacts and full SHA-256 coverage.
- Reports planned, captured, validated and invalid states plus unexpected capture folders.
- Flags unknown operator labels for review without treating them as ground truth.
- Added synthetic tests for empty plans, full checksum coverage, missing checksum, wrong checkpoint, unexpected folders and session identity mismatch.
- No real gameplay captures or room-classification accuracy are claimed.

## Unreleased — RGM-001E.15 Capture Synchronization & Temporal Consistency

- Added temporal evidence auditor for paired state and graphics dump intervals.
- Added monotonic-clock interval checks, configurable midpoint-gap review and optional frame-marker equality.
- Missing frame markers remain review-required; timestamp proximity alone cannot prove a frozen game state.
- Added repeated-checkpoint timing summaries without comparing frame numbers across separate repeats.
- Added synthetic tests for matched/mismatched frames, large gaps, missing evidence, invalid intervals and clock metadata.
- No runtime frame instrumentation or real synchronized game captures are claimed.

## Unreleased — RGM-001E.16 Runtime Capture Bundle Adapter

- Added a staged C++ adapter to invoke the existing upstream state and graphics dump APIs on the emulation thread.
- Added monotonic host timestamps and stable completed-frame epoch sampling before/after each dump.
- Added metadata with session/experiment/checkpoint/repeat identity and observed labels.
- Added SHA-256 finalizer for state, summary and graphics artifacts, with required image checks and path/symlink safeguards.
- Temporal auditor now consumes explicit runtime frame-stability flags.
- Added synthetic tests for checksum finalization, missing graphics, path traversal, symlinks and unstable frame evidence.
- Adapter is not yet wired into or compiled against upstream; no real game capture is claimed.
