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

Current work: **RGM-001E.10 — Real Gameplay Capture Ingestion**.

The offline Snapshot Analyzer compares WRAM, HRAM, IO and OAM snapshot blocks. The conservative Scene State Classifier reports UI-family and dialogue-geometry candidates, while leaving unvalidated scene types and character/speaker identity unresolved. The Graphics Comparator compares upstream RGBA framebuffer, tile sheets and 32×32 tilemap cells. The experimental Room Fingerprint Engine hashes rendered tile patterns and tests circular tilemap offsets to report candidate similarity. Synthetic tests are not game-runtime validation; no real game snapshot dataset or Android build is claimed.

See:
- [Roadmap](docs/ROADMAP.md)
- [Architecture and provenance](docs/ARCHITECTURE.md)
- [RGM-001E dataset and fingerprint protocol](docs/analysis/RGM-001E-SNAPSHOT-PROTOCOL.md)
- [Room Fingerprint Engine](tools/ROOM-FINGERPRINT.md)
- [Snapshot Analyzer](tools/rgm_snapshot_analyzer.py)
- [Graphics Comparator](tools/rgm_graphics_comparator.py)
- [Room Fingerprint Tool](tools/rgm_room_fingerprint.py)\n- [Scene State Classifier](tools/rgm_scene_classifier.py)\n- [Scene Classification Specification](tools/SCENE-STATE-CLASSIFICATION.md)
- [Controlled Gameplay Experiments](docs/analysis/RGM-001E.9-CONTROLLED-EXPERIMENTS.md)
- [Experiment Matrix](docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json)
- [Experiment Plan Generator](tools/rgm_experiment_plan.py)
- [Real Capture Ingestion](docs/analysis/RGM-001E.10-REAL-CAPTURE-INGESTION.md)

## Legal and asset policy

The upstream source license does not grant rights to the original game ROM, Capcom trademarks, commercial artwork, dialogue, music or other proprietary assets. Do not commit ROMs, copyrighted game assets, BIOS files or extracted proprietary content. Use legally obtained local game data for private testing and keep generated or original replacement artwork clearly identified.

## Reproducibility

Record the upstream commit, tool version, capture metadata and SHA-256 checksums for every dataset. Never report a build, device test, patch or game-state conclusion unless it has actually been performed and logged.
