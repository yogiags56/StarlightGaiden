# RGM-001E.25 — Exploration State Mapping

## Purpose

Map the runtime state changes caused by controlled exploration inputs without changing rooms. This stage follows the review of ten Android captures in RGM-001E.24.

## Evidence carried forward

The tenth reviewed capture was identified as top-down exploration. Its recorded observations were:

- WRAM bank: 1
- SCX: 0xB8
- SCY: 0xFD
- Active OAM sprites: 4
- The two exported tilemaps showed the same room structure.

These are observations from one capture, not yet a verified room signature or a complete player-position model. Do not infer Barry's coordinates, facing, movement state, or room identity from these values alone.

## Controlled capture sequence

Keep the game in one room throughout the sequence. Record the exact input, duration/frame count, and visible result for every capture.

| ID | Player condition | Required observation |
|---|---|---|
| EXP-00 | Barry stationary (baseline) | Stable state and graphics baseline |
| EXP-01 | Walk north | State deltas and visible displacement |
| EXP-02 | Walk east | State deltas and visible displacement |
| EXP-03 | Walk south | State deltas and visible displacement |
| EXP-04 | Walk west | State deltas and visible displacement |
| EXP-05 | Stationary after movement | Separate persistent position from transient animation |
| EXP-06 | Face/interact with a door | Input response, object state, and any transition trigger |
| EXP-07 | Interact with a nearby object | Object interaction response without leaving the room |

If a direction is blocked by geometry, record it as blocked; do not substitute a different action. If an interaction changes rooms, stop that sequence and mark the transition rather than treating it as an in-room observation.

## Required paired evidence

For each observation, collect:

1. Memory snapshot binary and its text summary.
2. Graphics capture directory containing both tilemaps, framebuffer, tile sheets, and manifest.
3. Capture metadata linking the exact memory and graphics files.
4. SHA-256 checksums for every raw artifact.
5. Input/action log with start/end frame or duration.
6. Operator-confirmed room label and visible Barry position/facing where observable. Use `unknown` when not directly observable.

Memory and graphics exports are not atomic. Record timing and frame-counter evidence independently for both dumps. A close timestamp alone does not prove that both exports represent the same game frame.

## Analysis procedure

For each paired state:

- Run `tools/rgm_snapshot_analyzer.py` on the stationary baseline and each movement/interact snapshot.
- Compare WRAM changes by 4 KiB bank, then inspect stable repeated offsets across same-action captures.
- Compare HRAM, IO, and OAM separately; do not assume every OAM change is player animation.
- Inspect SCX/SCY alongside tilemap and framebuffer differences to separate camera scrolling from player movement.
- Compare both tilemaps to detect room-structure changes. A changed map is a possible transition/loading event, not automatic proof of a new room.
- Run the temporal consistency auditor and strict ingestion reviewer before using a capture as training or calibration evidence.

## Mapping rules

A candidate field may be called a player-position signal only when it:

1. Changes consistently with visible movement in the expected direction.
2. Remains stable when Barry stops.
3. Is distinguishable from camera scroll and animation-frame changes.
4. Repeats across multiple movement trials.
5. Does not show the same behavior in unrelated UI, object, or animation changes.

A candidate facing signal must distinguish the four directions across repeated stationary-facing observations. An interaction signal must be separated from the resulting animation, sound/UI response, and room transition.

Keep raw offsets and observed values in the report. Do not assign semantic names to addresses until the evidence supports them. Preserve competing hypotheses and negative results.

## Exit criteria

RGM-001E.25 is complete only when:

- All available captures pass file-integrity checks.
- Each capture has explicit state/graphics pairing and timing evidence.
- At least one repeat exists for each usable movement direction.
- Candidate position/facing signals are supported by repeated observations and negative controls.
- Door/object interactions are classified as in-room response, blocked/no response, or room transition.
- A mapping report documents unresolved fields and confidence limits.

Synthetic tests may validate the analysis tools, but cannot satisfy the gameplay-evidence criteria. Do not calibrate room or scene classifiers from this stage alone.
