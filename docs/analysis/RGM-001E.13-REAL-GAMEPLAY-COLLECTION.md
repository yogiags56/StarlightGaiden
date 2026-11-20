# RGM-001E.13 — Real Gameplay Dataset Collection

## Objective
Turn the controlled experiment matrix into an auditable collection session and report progress without manufacturing game data.

## Create a session
From the repository root:
```bash
python tools/rgm_experiment_plan.py \
  --matrix docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json \
  --output dataset/SESSION-0001 \
  --session-id SESSION-0001
```

The generator creates a session plan and one `FP-<capture_id>` folder per checkpoint. It writes metadata templates and an empty graphics folder only. It does not create a state dump, game screenshot, ROM, or real capture.

The current matrix contains 11 experiments, 45 checkpoints and 3 repeats (135 planned capture records).

## Capture protocol
For each checkpoint, use a legally obtained local game copy and the upstream runtime's state dump and asset dump actions. Keep the game state unchanged while taking the paired dumps. Copy the matching files into the corresponding folder:
- `state.bin` — binary state snapshot.
- `state.txt` — state summary.
- `graphics/framebuffer.png`, `graphics/map_9800.png`, `graphics/map_9c00.png`.
- `graphics/manifest.txt` and the upstream tile/palette PNG exports.
- `capture_metadata.json` — update observed location/activity/character/speaker and actual checkpoint/repeat details.
- `source_sha256` — SHA-256 for every required artifact, using paths relative to the capture folder.

Do not change the game state between the state and graphics dump. If it changes, discard the pair or record the deviation and repeat it. Keep raw originals unchanged.

## Progress audit
```bash
python tools/rgm_collection_status.py dataset/SESSION-0001 \
  --output dataset/SESSION-0001/collection_status.json
```

Statuses:
- `planned`: capture templates exist, but paired data is not present.
- `captured`: core state/summary/graphics files exist, but strict validation or checksum provenance is incomplete.
- `validated`: the capture validator accepts the state snapshot, summary, graphics dimensions/manifest and recorded SHA-256 checksums.
- `invalid`: metadata identity or path checks fail.

Validation does not verify the room label, active character, speaker, or scene identity. Those require separate human review and ground-truth annotations.

## Next processing
After collection:
```bash
python tools/rgm_capture_validator.py dataset/SESSION-0001 --output capture_validation.json
python tools/rgm_dataset_audit.py dataset/ --output dataset_audit.json --split-manifest dataset_split_manifest.json
```
Use verified annotation and calibration/holdout evaluation only after independent groups and human-reviewed room labels exist.

## Integrity and limitations
- Do not commit ROMs or extracted proprietary assets.
- Keep dataset manifests, hashes and source commit references with the capture set.
- Repeated captures from one session are not independent samples; the dataset auditor groups them together.
- The current status tool reports file/provenance readiness only. It does not score room fingerprint accuracy.
- No real gameplay captures are included or claimed by this milestone.
