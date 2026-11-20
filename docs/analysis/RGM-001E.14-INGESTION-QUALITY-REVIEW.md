# RGM-001E.14 — Real Capture Ingestion & Dataset Quality Review

## Purpose
Review a planned capture session against its generated plan and validate exact capture provenance before dataset analysis. The reviewer is read-only: it does not rewrite metadata, repair checksums, or fabricate game data.

## Run
From the repository root:
```bash
python tools/rgm_ingestion_review.py dataset/SESSION-0001 \
  --output dataset/SESSION-0001/ingestion_review.json
```

## Status rules
- `planned`: the template exists but no state snapshot, summary, or graphics artifacts have been collected.
- `captured`: some capture artifacts exist, but required files or exact checksum coverage are incomplete.
- `validated`: capture ID, session ID, experiment ID, checkpoint and repeat match the session plan; the strict upstream-format validator passes; all discovered required artifacts have matching SHA-256 entries.
- `invalid`: identity mismatch, malformed capture data, unsafe path, or checksum mismatch.
- Unexpected `FP-*` folders are separately reported and prevent session completion.

The report also flags unknown/unrecorded location, activity, character and speaker labels for operator review. Such warnings do not establish identity.

## Required provenance
Each planned capture must retain:
- state snapshot binary and state summary;
- graphics directory containing framebuffer, both tilemaps, manifest and exported graphics;
- metadata identifying session, experiment, checkpoint and repeat;
- SHA-256 entries for every state and graphics artifact discovered by the reviewer.

Do not add the metadata file itself to its own checksum list. Preserve original dump files unchanged.

## Follow-up
After the review, run the existing dataset audit:
```bash
python tools/rgm_dataset_audit.py dataset/ \
  --output dataset_audit.json \
  --split-manifest dataset_split_manifest.json
```
Only validated captures enter the dataset audit. Observed operator labels remain unverified grouping hints, not ground truth.

## Limitations
- This tool checks structural consistency and integrity, not whether two captures represent the same room.
- It does not verify active character or dialogue speaker.
- Synthetic fixtures validate the tool only; no real gameplay captures are included.
- ROMs and proprietary game assets must remain local and must not be committed.
