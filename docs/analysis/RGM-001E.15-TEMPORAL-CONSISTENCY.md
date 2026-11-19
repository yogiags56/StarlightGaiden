# RGM-001E.15 — Capture Synchronization & Temporal Consistency

## Purpose
Assess whether a state snapshot and graphics dump can be treated as a paired observation of one game state. The auditor distinguishes measured timing from actual frame identity; timestamps alone cannot prove that gameplay did not advance between dump operations.

## Optional capture metadata
Add a `capture_timing` object to each capture's `capture_metadata.json` when the capture harness can record it:

```json
{
  "capture_timing": {
    "clock_id": "monotonic:SESSION-0001",
    "clock_source": "time.monotonic_ns",
    "state_dump_started_ns": 1000000000,
    "state_dump_completed_ns": 1020000000,
    "graphics_dump_started_ns": 1030000000,
    "graphics_dump_completed_ns": 1050000000,
    "game_frame_at_state": 1200,
    "game_frame_at_graphics": 1200
  }
}
```

All nanosecond values must come from the same monotonic clock and clock domain. Do not mix wall-clock epoch timestamps with monotonic values. The frame counter must be obtained from a trustworthy runtime hook and sampled as close as possible to the actual dump operation; never invent a frame number from timestamps.

If the runtime cannot expose a stable frame counter, omit both frame fields. The auditor will mark the pair `review_required`, even when timestamps are close. A small timing gap is supporting evidence only.

## Run
```bash
python tools/rgm_temporal_consistency.py dataset/SESSION-0001 \
  --max-gap-ms 250 \
  --output dataset/SESSION-0001/temporal_review.json
```

The default 250 ms is a provisional review window, not a scientifically calibrated threshold. Change it only with a documented rationale and retain the selected value in the output.

## Statuses
- `time_window_pass`: valid intervals, same clock ID, midpoint gap within limit, and matching frame markers.
- `review_required`: timing is too far apart or does not prove frame identity.
- `insufficient_evidence`: metadata/timing is absent.
- `invalid`: malformed intervals or contradictory frame markers.

The tool groups repeated checkpoints by experiment and checkpoint, but does not expect the frame number from repeat 1 to equal repeat 2. Those are distinct moments in gameplay.

## Capture harness requirements for stronger evidence
1. Use one monotonic clock source for the entire session.
2. Record start/end around both dump operations.
3. If possible, pause/freeze game updates while taking both dumps, or expose a reliable game-frame counter and read it atomically at each dump.
4. Record whether the game was paused, whether a transition occurred, and any capture interruption.
5. Preserve raw files and metadata; do not patch timestamps after collection.

## Limitations
- Upstream state/asset dump APIs inspected so far do not expose a shared frame ID or atomic paired-capture operation. The new tool only evaluates metadata supplied by a future/local capture harness.
- Matching frame markers are only as trustworthy as the runtime instrumentation that records them.
- This is a temporal evidence audit, not room identity or scene classification.
- No real game capture or synchronization result is claimed by synthetic tests.
