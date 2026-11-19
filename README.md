# Resident Evil Gaiden Remastered — StarlightGaiden

**StarlightGaiden** is the canonical development repository for Resident Evil Gaiden Remastered.

## Project direction

- **Target:** Android, ARM64-v8a primary.
- **Presentation:** hybrid 2D remaster with HD, semi-realistic artwork; not a full 3D remake.
- **Gameplay:** preserve the original Game Boy Color story, systems, pacing, puzzles, exploration and combat.
- **Aspect ratio:** preserve proportions; never stretch the game image.
- **Engineering:** source-first, modular, reproducible, with documented tests and provenance.

## Upstream foundation

The current technical candidate is [sergiomanzur/regaiden-recomp](https://github.com/sergiomanzur/regaiden-recomp), a separate upstream project. This repository is the project workspace for our analysis, tools, documentation and future integration work. Upstream code is not copied or modified here unless its exact source, commit, license and changes are recorded.

## Development status

Current work: **RGM-001E.21 — Android ARM64 APK built and package-verified in CI; physical-device validation pending**

The offline Snapshot Analyzer compares WRAM, HRAM, IO and OAM snapshot blocks. The conservative Scene State Classifier reports UI-family and dialogue-geometry candidates, while leaving unvalidated scene types and character/speaker identity unresolved. The Graphics Comparator compares upstream RGBA framebuffer, tile sheets and 32×32 tilemap cells. The experimental Room Fingerprint Engine hashes rendered tile patterns and tests circular tilemap offsets to report candidate similarity. Synthetic tests are not game-runtime validation; no real game snapshot dataset or physical-device runtime validation is claimed.

See:
- [Roadmap](docs/ROADMAP.md)
- [Android ARM64 CI build report](docs/analysis/RGM-001E.21-ANDROID-ARM64-CI.md)
- [Architecture and provenance](docs/ARCHITECTURE.md)
- [RGM-001E dataset and fingerprint protocol](docs/analysis/RGM-001E-SNAPSHOT-PROTOCOL.md)
- [Room Fingerprint Engine](tools/ROOM-FINGERPRINT.md)
- [Snapshot Analyzer](tools/rgm_snapshot_analyzer.py)
- [Graphics Comparator](tools/rgm_graphics_comparator.py)
- [Room Fingerprint Tool](tools/rgm_room_fingerprint.py)
- [Scene State Classifier](tools/rgm_scene_classifier.py)
- [Scene Classification Specification](tools/SCENE-STATE-CLASSIFICATION.md)
- [Controlled Gameplay Experiments](docs/analysis/RGM-001E.9-CONTROLLED-EXPERIMENTS.md)
- [Experiment Matrix](docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json)
- [Experiment Plan Generator](tools/rgm_experiment_plan.py)
- [Real Capture Ingestion](docs/analysis/RGM-001E.10-REAL-CAPTURE-INGESTION.md)
- [Dataset Audit & Ground-Truth Evaluation](docs/analysis/RGM-001E.11-DATASET-AUDIT.md)
- [Dataset Audit Tool](tools/rgm_dataset_audit.py)
- [Verified Ground-Truth Evaluation](docs/analysis/RGM-001E.12-GROUND-TRUTH-EVALUATION.md)
- [Ground-Truth Evaluator](tools/rgm_ground_truth_evaluator.py)
- [Real Gameplay Dataset Collection](docs/analysis/RGM-001E.13-REAL-GAMEPLAY-COLLECTION.md)
- [Collection Status Auditor](tools/rgm_collection_status.py)
- [Ingestion Quality Review](docs/analysis/RGM-001E.14-INGESTION-QUALITY-REVIEW.md)
- [Strict Ingestion Reviewer](tools/rgm_ingestion_review.py)
- [Temporal Consistency Auditor](tools/rgm_temporal_consistency.py)
- [Temporal Consistency Protocol](docs/analysis/RGM-001E.15-TEMPORAL-CONSISTENCY.md)
- [Runtime Capture Bundle Adapter](docs/analysis/RGM-001E.16-RUNTIME-CAPTURE-ADAPTER.md)
- [Runtime Capture Bundle Source](integration/regaiden-recomp/rgm_capture_bundle.cpp)
- [Guarded Upstream Integration Script](integration/regaiden-recomp/apply_rgm_adapter.py)
- [C++ Adapter Smoke Test](tests/cpp_adapter_smoke.cpp)
- [Capture SHA-256 Finalizer](tools/rgm_capture_finalize.py)

## Legal and asset policy

The upstream source license does not grant rights to the original game ROM, Capcom trademarks, commercial artwork, dialogue, music or other proprietary assets. Do not commit ROMs, copyrighted game assets, BIOS files or extracted proprietary content. Use legally obtained local game data for private testing and keep generated or original replacement artwork clearly identified.

## Reproducibility

Record the upstream commit, tool version, capture metadata and SHA-256 checksums for every dataset. Never report a build, device test, patch or game-state conclusion unless it has actually been performed and logged.
