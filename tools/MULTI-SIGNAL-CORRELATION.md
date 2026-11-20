# RGM-001E.7 — Multi-Signal Scene Correlation

## Purpose
Correlate independent evidence from paired game-state and graphics captures. This is an evidence layer, not a room/scene/character classifier.

## Signals
- Environment: compare both rendered 32×32 maps (map_9800 and map_9c00) using camera-offset tile fingerprints.
- Runtime: parse the actual upstream state_dump.c summary format: ROM bank, WRAM bank, PC/SP, LCD registers and active sprite entries.
- Memory transition: report changed bytes by WRAM/HRAM/IO/OAM and WRAM bank. High change counts do not imply a different room.
- Camera: report circular 8-bit SCX/SCY deltas.
- Sprite state: compare active OAM summary and raw 160-byte OAM block.
- Audio hint: read ctx->wram[0x0E8C], matching upstream gb_state_music_track; only IDs 0..27 are retained. Music is weak context, not scene identity.

## Run
```bash
python tools/rgm_scene_correlator.py dataset/ --output scene_correlation.json
```
Dataset must pass capture integrity validation first.

## Output
- strong_correlation_candidate: high provisional map similarity plus at least one contextual corroborator.
- weak_correlation_candidate: moderate provisional map similarity.
- insufficient_evidence: inadequate map evidence.
These describe pairwise evidence only. No room, scene, active character or speaker identity is asserted.

## Limitations
No actual game captures are present; tests use synthetic data. Rendered map PNGs do not expose raw VRAM tile IDs/CGB attributes. ROM bank, PC, WRAM bank, OAM and music may vary within a room or persist across scene changes. Thresholds are provisional and require labeled real-game positive and negative examples.
