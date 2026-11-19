# RGM-001E.8 — Scene State Classification Foundation

## Purpose
Build a conservative per-capture scene evidence report for eight target scene types: exploration, dialogue, cutscene, inventory/PDA, normal combat, boss combat, room transition and save/load.

## Source-backed indicators
1. UI family: upstream game_state.h uses normalized WRAM bank 2 for UI screens; SVBK 0 aliases bank 1. The source comments report inventory, item info, PDA, title menu and save menu in bank 2. This does not distinguish those subtypes.
2. Dialogue candidate: upstream hd_pack.c uses LCDC window enable, WX <= 166, not UI bank, and WY 72..134. The tool reports a candidate only; the geometry is not a verified speaker/dialogue identifier.
3. Music track: read from WRAM offset 0x0E8C, retained as context only.

## Run
```bash
python tools/rgm_scene_classifier.py dataset/ --output scene_states.json
```

## Conservative output
The tool emits `ui_screen_family`, `dialogue`, or `unclassified` candidates. It does not assign any of the eight target scene types as verified labels. Per-type states remain `unresolved` until discriminators are validated using real captures.

## Explicit unknowns
Exploration versus intro cutscene; normal versus boss combat; room transition; save/load; inventory versus PDA versus title/save menu; active character; speaker. Do not promote ROM bank, PC, music, HP values or sprite count to unique identifiers without controlled capture experiments.

## Validation
Synthetic tests exercise UI-family handling, dialogue geometry and the unknown fallback. They do not validate game behavior. Real labeled captures and negative controls are required before calibration.
