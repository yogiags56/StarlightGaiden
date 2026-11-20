# RGM-001E.9 — Controlled Gameplay Capture Experiments

## Goal
Collect repeatable, paired state_dump and asset_dump observations to test the scene classifier and room fingerprint matcher. The experiment matrix is [RGM-001E.9-EXPERIMENT-MATRIX.json](RGM-001E.9-EXPERIMENT-MATRIX.json).

## Capture discipline
1. Use a legally obtained local game ROM and a consistent upstream build/commit.
2. At every checkpoint, capture the state snapshot and graphics dump without advancing or changing game state between the two operations. If the UI requires separate actions, record the exact sequence and flag the pair as non-atomic.
3. Repeat each controlled experiment three times where feasible.
4. Record observed facts only. Keep location label, activity, character and speaker as unknown unless directly observed; these are labels for evaluation, not classifier outputs.
5. Preserve both positive and negative controls: same room with movement/camera changes, visually similar different rooms, UI open/closed, combat entry/exit and cutscene transitions.
6. Never overwrite a capture. Use a new session/capture ID and record SHA-256 hashes.
7. Run the capture validator before correlator/classifier. Invalid or incomplete pairs must not enter evaluation.

## Matrix coverage
- EXP-01 exploration baseline and movement
- EXP-02 inventory/item detail
- EXP-03 PDA and menu pages
- EXP-04 dialogue and speaker changes
- EXP-05 ordinary combat
- EXP-06 boss combat
- EXP-07 room transitions versus camera scroll
- EXP-08 cutscenes, including intro paths
- EXP-09 save/load
- EXP-10 Barry/Leon/Lucia identity controls
- EXP-11 visually similar rooms as negative controls

## Generate a blank session plan
```bash
python tools/rgm_experiment_plan.py --output dataset/SESSION-0001 --session-id SESSION-0001
```
The generator creates only JSON templates and directories. It does not fabricate snapshots or graphics. Fill metadata after actual capture and add SHA-256 values using the validator's expected relative-path format.

## Acceptance gates
- At least three repeated samples for each reachable state transition.
- Paired state and graphics captures for each checkpoint.
- Positive controls: same room / same scene under movement, camera and animation changes.
- Negative controls: different room with similar visual structure; UI and non-UI; normal and boss encounter.
- No thresholds promoted to verified until false-positive and false-negative results are measured on held-out captures.
- Character and speaker identity require their own controlled experiments and must not be inferred from HP bytes alone.

## Current limitation
No actual game captures are included in this repository. This milestone supplies the experiment protocol and reproducible blank-plan generator only.
