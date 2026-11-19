# RGM-001E.10 — Real Gameplay Capture Ingestion

## Purpose
Make the controlled experiment plan and capture validator use one canonical directory layout, then reject incomplete or mismatched capture records before they enter analysis.

## Canonical layout
```text
dataset/
└── SESSION-0001/
    ├── session_plan.json
    ├── FP-EXP-01-CP-01-R01/
    │   ├── capture_metadata.json
    │   ├── state.bin
    │   ├── state.txt
    │   └── graphics/
    │       ├── framebuffer.png
    │       ├── map_9800.png
    │       ├── map_9c00.png
    │       ├── manifest.txt
    │       └── tiles_*.png
    └── FP-EXP-01-CP-01-R02/
        └── ...
```

Capture IDs remain independent from directory names: directory is `FP-<capture_id>`, and `capture_metadata.json` contains that exact capture ID plus the session ID. The parent session directory must match `session_id`.

## Ingestion checks
The validator checks:
- Metadata schema and required capture/session identifiers.
- Capture ID and session directory identity.
- Safe relative paths; paths escaping the capture directory are rejected.
- Parseable state snapshot binary.
- Present, non-empty state summary (missing ROM-bank field is a warning).
- Graphics directory and expected PNG files/dimensions: maps 256×256, framebuffer 160×144.
- Non-empty graphics manifest.
- SHA-256 of each listed source file when hashes are provided.
- Duplicate/invalid captures remain excluded from pairwise trials.

## Workflow
1. Generate blank templates with `tools/rgm_experiment_plan.py`.
2. Populate the template only after making a real upstream capture.
3. Copy the paired upstream state dump and graphics dump into the paths named by metadata.
4. Record observed labels and SHA-256 hashes; keep unverified identities explicitly unverified.
5. Run:
   ```bash
   python tools/rgm_capture_validator.py dataset/ --output dataset_validation.json
   ```
6. Only valid captures proceed to exploratory pair comparisons. Use:
   ```bash
   python tools/rgm_scene_correlator.py dataset/ --output scene_correlation.json
   ```

## Test guarantees and limitations
Synthetic integration tests verify that generated plans are discovered by the validator and rejected as incomplete until actual files are added. This is not a real gameplay test. The tool cannot prove that state and graphics dumps were taken atomically; the operator must follow and document the capture protocol. A passing integrity check means file structure and hashes are consistent, not that labels or game-state interpretations are correct.
