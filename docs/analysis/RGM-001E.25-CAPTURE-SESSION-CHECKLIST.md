# RGM-001E.25 — Device Capture Session Checklist

This checklist operationalizes the exploration-state mapping experiment. It does not replace the experiment specification in `RGM-001E.25-EXPLORATION-STATE-MAPPING.md`.

## Before starting

- Install the current ARM64 debug APK and launch the game.
- Confirm the capture/export feature is available and that the output destination is `Downloads/StarlightGaiden`.
- Start in a room where Barry can be seen clearly and where the camera is not already scrolling.
- Record the game/ROM build identifier if displayed. Do not include or commit proprietary ROM data.
- Create one new session folder using the existing session-plan schema. Never reuse a prior session ID.

## Capture order

Capture each checkpoint as a paired memory + graphics export. Keep the same room for EXP-00 through EXP-05.

| Checkpoint | Action | Repeat |
|---|---|---:|
| EXP-00 | Barry stationary baseline; wait until animation settles | 2 |
| EXP-01 | Hold north briefly, release, then capture | 2 |
| EXP-02 | Hold east briefly, release, then capture | 2 |
| EXP-03 | Hold south briefly, release, then capture | 2 |
| EXP-04 | Hold west briefly, release, then capture | 2 |
| EXP-05 | After movement, remain stationary until transient animation settles | 2 |
| EXP-06 | Approach/face a visible door and attempt interaction once | 2 |
| EXP-07 | Approach a nearby visible object and attempt interaction once | 2 |

For every action, record the actual button(s), approximate hold duration or frame count, whether movement was blocked, and what visibly changed. Do not substitute another direction when blocked. If a door interaction changes rooms, stop and mark it as a transition; do not perform EXP-07 in the new room under the same room label.

## Required annotations

For each capture, fill in the generated `capture_metadata.json`:

- `observed.location_label`: operator-entered label; use `unknown` if uncertain.
- `observed.activity`: stationary, walk_north/east/south/west, door_interaction, or object_interaction.
- `observed.character`: Barry only if directly visible; otherwise unknown.
- `observed.facing`: north/east/south/west/unknown, only when directly observable.
- Record action input and duration/frame count in the capture's action log.
- Keep room/scene verification fields as unverified. Do not promote them based on visual guesswork.

## Finalize and validate

From the repository root, finalize every capture directory:

```sh
python3 tools/rgm_capture_finalize.py path/to/SESSION-ID/FP-CAPTURE-ID
```

Then inspect the complete session:

```sh
python3 tools/rgm_collection_status.py path/to/SESSION-ID
python3 tools/rgm_capture_validator.py path/to/dataset
```

Keep the original ZIP export unchanged. Upload the ZIP or the complete session folder to the project conversation for analysis. Do not commit raw gameplay captures, ROM files, save files, or proprietary game assets to the public repository.

## Stop conditions

- Stop if export fails, files are incomplete, the game crashes, or the player leaves the intended room unexpectedly.
- Do not infer Barry's memory addresses, coordinates, facing, room identity, or animation state from a single capture.
- Synthetic fixtures may test tooling but do not count as real gameplay evidence.

## Exit gate

RGM-001E.25 remains in progress until repeated usable direction captures, paired state/graphics evidence, timing records, checksum validation, and interaction classifications are reviewed. Only then may the project advance to position/facing signal mapping.
