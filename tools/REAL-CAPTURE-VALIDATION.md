# RGM-001E.6 — Real Capture Validation Harness

## Purpose
Validate paired memory/graphics capture integrity and produce exploratory pairwise fingerprint trials grouped by tester-entered location labels. Labels are not ground truth; the tool never verifies or assigns a room ID.

## Metadata schema (version 1)
Each `SESSION-*/FP-*/capture_metadata.json`:
```json
{
  "schema_version": 1,
  "session_id": "SESSION-0001",
  "capture_id": "FP-0001",
  "observed": {"location_label": "Starlight corridor A", "activity": "exploration", "character": "Barry"},
  "capture": {"state_file": "state_01.bin", "state_summary": "state_01.txt", "graphics_directory": "capture_0001"},
  "source_sha256": {"state_01.bin": "SHA256_HEX", "state_01.txt": "SHA256_HEX", "capture_0001/map_9800.png": "SHA256_HEX"}
}
```
Record SHA-256 for every raw file. Paths are restricted to the capture directory. Use `unknown` rather than guessing.

## Required files
- Valid upstream memory snapshot binary and its text summary.
- Graphics folder with `map_9800.png`, `map_9c00.png`, `framebuffer.png`, and `manifest.txt`.
- Both maps: 256×256 RGBA; framebuffer: 160×144 RGBA.
- Keep raw captures immutable; put reports in `derived/`.

## Run
```bash
python tools/rgm_capture_validator.py dataset/ --output dataset_validation.json
python -m unittest discover -s tests -v
```
Exit code 0: all captures valid; 1: invalid captures found; 2: invocation/dataset error.

## Evaluation
All pairs with known tester location labels are compared using rendered `map_9800.png`. The report counts same-label and different-label pairs and records candidate/weak/insufficient matcher outputs. This is exploratory, not an accuracy or false-positive metric. Validate labels independently, collect repeated same-room captures with camera/animation variation, and collect negative controls from distinct rooms with similar patterns.

## Limitations
No real game captures are currently present. Memory and graphics dumps are sequential, not atomic; record capture order and delay. `map_9c00.png` is checked but not yet included in scoring. Rendered RGBA does not expose raw VRAM tile IDs or CGB attributes. Thresholds remain provisional; no verified room ID or accuracy claim is permitted until a labeled real-game dataset exists.
