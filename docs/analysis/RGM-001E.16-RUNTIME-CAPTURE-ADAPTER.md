# RGM-001E.16 — Runtime Capture Bundle Adapter

## Status
Adapter source and host-side checksum finalizer are staged in this repository. They are not yet integrated into or compiled with the upstream recompilation project. No real game capture is claimed.

## Source files
- `integration/regaiden-recomp/rgm_capture_bundle.h`
- `integration/regaiden-recomp/rgm_capture_bundle.cpp`
- `tools/rgm_capture_finalize.py`

The C++ adapter calls the existing `state_dump_capture()` and `asset_dump_capture()` APIs. It writes both into one `FP-<capture_id>` folder and emits a metadata file containing experiment identity, monotonic-clock intervals, and frame-stability markers. It does not patch the ROM or guest state.

## Correct insertion point in upstream
In `src/recompiled/Resident_Evil_Gaiden__USA__main.c`, the normal SDL game loop:
1. Calls `gb_reset_frame(ctx)`.
2. Runs `gb_run_cycles()` until `ctx->frame_done`.
3. Increments local `frame_index`.
4. Calls optional port update/render.
5. Reads the framebuffer and calls `gb_platform_render_frame(fb)`.

For an automated capture, call `rgm_capture_bundle()` after the frame has completed and before the next `gb_reset_frame(ctx)` begins. The closest safe location in the normal SDL path is after the optional `gbrt_port_render()` and before `gb_get_framebuffer()/gb_platform_render_frame()`. This runs on the emulation/main thread with a completed guest frame. Do not call from a separate worker thread.

The benchmark/headless loop has a separate code path and currently does not render through the SDL frame path; do not assume the normal insertion point applies there.

## Frame token semantics
Upstream `GBContext.completed_frames` is incremented by `gb_reset_frame()` when the preceding frame has completed. Therefore, at the post-frame/pre-next-reset insertion point it is a stable zero-based frame epoch token for the frame just completed. It advances when the next frame begins. The adapter samples it before and after each dump; all four samples must agree.

This token is not a hardware timestamp or sub-frame PPU position. It proves only that the runtime did not cross a guest-frame boundary between the paired dump operations. The adapter also records monotonic host-clock start/end times. The two dumps are sequential, not atomic; any in-frame mutation by an asynchronous thread would require separate investigation. The emulator must remain single-thread-owned during this call.

## Integration instructions
Against the audited upstream commit `e5befd20e67939d939319149d1c1177b8e6c5cd6`:
1. Copy the two adapter files into the upstream `src/recompiled/` directory (or another location in the same native target).
2. Add `rgm_capture_bundle.cpp` to the native executable/library target in its CMake source list. Keep `state_dump.c` and `asset_dump.c` linked as they already are.
3. Ensure the target uses C++17 or newer (`std::filesystem`); the audited build is configured for C++20.
4. Include `rgm_capture_bundle.h` in the game-loop translation unit.
5. Add an explicit, opt-in capture trigger after the completed-frame/port-render block and before framebuffer presentation. Populate the IDs from the planned session JSON; never infer character/speaker labels from HP bytes.
6. Build desktop first, then Android ARM64. Keep the feature disabled by default and preserve normal gameplay when disabled.

Illustrative call:
```cpp
char capture_status[512] = {};
const bool captured = rgm_capture_bundle(
    ctx,
    "dataset/SESSION-0001/FP-EXP-01-CP-01-R01",
    "SESSION-0001",
    "EXP-01-CP-01-R01",
    "EXP-01",
    "stationary",
    1,
    "Starlight corridor",
    "exploration",
    "Barry",
    "none",
    capture_status,
    sizeof(capture_status));
fprintf(stderr, "[RGM] %s\\n", capture_status);
```

This is an example only. The capture directory must be unique and the labels must be operator-confirmed. Do not capture every frame by default; disk I/O and PNG export are intentionally opt-in.

## Finalize and review
After each successful capture:
```bash
python tools/rgm_capture_finalize.py dataset/SESSION-0001/FP-EXP-01-CP-01-R01
python tools/rgm_ingestion_review.py dataset/SESSION-0001 --output dataset/SESSION-0001/ingestion_review.json
python tools/rgm_temporal_consistency.py dataset/SESSION-0001 --output dataset/SESSION-0001/temporal_review.json
```

The finalizer hashes the state binary, state summary, and every file in the graphics directory. It refuses missing required graphics, path traversal and symlink artifacts. It updates only the metadata checksum map; the raw dump files remain unchanged.

## Known limitations / next gates
- The adapter is a proposal staged in StarlightGaiden, not an upstream patch.
- It has not been compiled against upstream headers or tested in the emulator.
- The upstream state dump function currently ignores individual `fwrite()` return values; the ingestion validator must continue checking file structure and expected sizes.
- The adapter checks expected state/summary files and graphics directory creation, but full PNG integrity and binary snapshot integrity are still enforced by downstream validators.
- `state_dump_set_output_dir()` and its count are process-global; serialize capture requests and do not run multiple bundles concurrently.
- The current adapter uses `ctx->completed_frames` as a stable frame epoch, not a PPU scanline or dot counter.
- No ROM, commercial artwork, music, or proprietary game assets are committed.
