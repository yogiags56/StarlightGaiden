# RGM-001E.5 — Room Fingerprint Engine

## Purpose

Generate a visual tile-pattern fingerprint from a 256×256 RGBA tilemap export and compare two captures while testing small circular tile offsets. The circular alignment models a 32×32 scrolling/ring-buffer tilemap; it does not establish world coordinates.

## Usage

Fingerprint one tilemap:

```bash
python tools/rgm_room_fingerprint.py capture_a/map_9800.png --output fp_a.json
```

Compare two captures:

```bash
python tools/rgm_room_fingerprint.py capture_a/map_9800.png capture_b/map_9800.png \
  --max-shift 8 --min-overlap 96 --output room_match.json
```

Exclude known dynamic/unstable tile positions (coordinates are tile indices, not pixels):

```json
{
  "exclude_cells": [[0, 0], [1, 0], [2, 0]]
}
```

Pass masks independently with `--exclude-a` and `--exclude-b`. Exclusions must be evidence-based and documented; do not mask large areas simply to force a match.

## Fingerprint model

- Each 8×8 RGBA tile cell is SHA-256 hashed (truncated to 96 bits for the in-memory cell token).
- A sorted multiset digest is translation-invariant but ignores tile arrangement; it is a coarse descriptor only.
- Pairwise matching tests circular shifts in the configured range.
- Similarity is inverse-frequency weighted so common repeated tiles contribute less than rarer patterns.
- Overlap count is reported independently; a high score on a tiny overlap is not accepted.
- A minimum of four distinct tile patterns is required in the best overlap. Uniform/repetitive maps are rejected as ambiguous even when pixel-identical.

## Output states

- `candidate_match`: provisional score and overlap gates passed.
- `weak_candidate`: overlap gate passed but similarity is moderate.
- `insufficient_evidence`: overlap too small or similarity too weak.

Default gates (0.82 similarity, 96 overlapping cells, four distinct patterns) are initial engineering values, not measured accuracy. They must be calibrated against real captures and negative controls before use in gameplay.

## Important limitations

1. The source PNG has CGB bank, palette and flip rendering baked into pixels. It does not expose original tile IDs or attributes.
2. Animated tiles, palette cycling and transient graphics can change the visual hash. Temporal capture and evidence-based masks are required.
3. Circular shifts model a ring buffer, not arbitrary camera movement in world coordinates. Large shifts and room boundaries need more captures.
4. A repeated pattern (corridor, blank wall, floor) can create false positives. The report is only a candidate comparison.
5. No verified room ID, scene ID, active character or speaker is assigned by this tool.
6. This milestone has synthetic tests only until actual paired game captures are supplied.
