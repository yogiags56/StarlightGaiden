# RGM-001E.11 — Dataset Audit & Ground-Truth Evaluation

## Purpose
Audit capture provenance, detect exact duplicate evidence, and create deterministic session-grouped train/calibration/evaluation manifests without leaking captures from one recording session across splits.

## Tool
`tools/rgm_dataset_audit.py`

Run:
```bash
python tools/rgm_dataset_audit.py dataset/ \
  --seed 20261119 \
  --output dataset_audit.json \
  --split-manifest dataset_split_manifest.json
```

Default proportions are 60% train, 20% calibration and 20% evaluation. Assignment is deterministic for a fixed dataset and seed.

## Audit rules
- Reuse the capture validator; invalid captures are excluded and listed with errors.
- Hash the state binary, state summary, two rendered tilemaps, framebuffer and graphics manifest.
- Detect exact duplicate evidence by a SHA-256 signature of available artifact hashes.
- Join captures from the same recording session and exact duplicates into one connected group.
- Assign whole groups, never individual captures, to one split.
- Quarantine unknown/unlabelled location labels.
- Reject duplicate capture IDs and invalid split ratios.
- Preserve observed labels as operator-supplied annotations, not verified ground truth.

## Evaluation safeguards
- A split is marked structurally ready only when at least three independent eligible groups exist and each split receives a group.
- This readiness flag does not establish class balance, room identity correctness, speaker/character truth, sufficient sample size or model performance.
- The tool does not train a model, tune thresholds, infer room IDs, or compute accuracy/precision/recall.
- The report includes exact duplicate groups, session groups, artifact hashes, split assignment, quarantined IDs and label-to-session counts.
- Re-run with the same seed to reproduce the same assignment for an unchanged dataset. Any changed artifact can change group identity and assignment; preserve the emitted manifest alongside the dataset version.

## Important limitations
The current room fingerprint is based on rendered RGBA tilemap images. Exact file hashes detect exact duplicates only; visually equivalent captures with different compression/metadata may not be deduplicated. Session grouping is a conservative leakage guard, not a substitute for verified room labels. A capture session spanning multiple locations remains grouped together to prevent temporal/session leakage.

No real-game dataset is included. Synthetic tests validate the audit mechanics only.
