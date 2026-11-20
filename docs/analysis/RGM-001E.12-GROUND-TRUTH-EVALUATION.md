# RGM-001E.12 — Verified Ground-Truth Evaluation

## Purpose
Introduce an auditable human-verified room annotation format and calibrate the experimental rendered-map similarity threshold without using holdout evaluation pairs.

## Required inputs
1. Dataset split manifest produced by `rgm_dataset_audit.py`.
2. Human-reviewed annotation file.
3. Pairwise correlation report produced by `rgm_scene_correlator.py`.

Example annotation:
```json
{
  "schema_version": 1,
  "annotations": [
    {
      "capture_id": "EXP-01-CP-01-R01",
      "room_id": "ST-ROOM-CORRIDOR-01",
      "verified": true,
      "reviewer": "reviewer-1",
      "evidence": "Same fixed room landmarks and connected doorway layout checked against the game capture."
    }
  ]
}
```

Every accepted annotation requires `verified: true`, a non-empty reviewer and an evidence note. Unverified annotations are ignored. The tool does not infer room IDs or decide whether a reviewer's evidence is correct.

## Run
```bash
python tools/rgm_ground_truth_evaluator.py \
  dataset_split_manifest.json \
  verified_room_annotations.json \
  scene_correlation.json \
  --output ground_truth_evaluation.json
```

## Evaluation policy
- Pair labels are derived only from explicit verified room IDs.
- A pair is eligible only when both captures have verified annotations and belong to the same calibration or evaluation split.
- Cross-split pairs are excluded.
- Threshold selection uses calibration pairs only and maximizes balanced accuracy; ties use F1 and then prefer the higher threshold.
- The selected threshold is applied once to evaluation pairs. Evaluation scores never influence threshold selection.
- Calibration requires both same-room and different-room pairs.
- Reports confusion counts, accuracy, precision, recall, specificity, F1 and balanced accuracy, plus skipped-pair reasons.

## Limitations
- The score currently uses mean available rendered-map fingerprint similarity from the correlator; it is not a learned classifier.
- Metrics are descriptive and do not include confidence intervals.
- Pairwise evaluation on a small number of rooms is not evidence of generalization to unseen rooms or scene classes.
- Ground-truth correctness remains a human review responsibility.
- No real game captures or verified room annotations are included in this repository.
