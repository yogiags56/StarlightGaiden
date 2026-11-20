# RGM-001E — Snapshot Dataset and Fingerprint Protocol

## Capture pairing

Each gameplay observation must pair one memory snapshot (`.bin` + `.txt`) with one graphics capture directory generated as close together as possible. Record the order and any input/frame delay between the captures. They are not an atomic capture.

The upstream memory snapshot currently stores:
- WRAM: 8 × 4 KiB
- HRAM: 0x7F bytes
- IO: 0x80 bytes
- OAM: 0xA0 bytes

It does **not** include VRAM or the complete PPU structure. The graphics dump separately exports:
- two VRAM banks × BG/OBJ sheets × eight palettes
- `map_9800.png` and `map_9c00.png`
- `framebuffer.png` at native 160×144
- `manifest.txt`

Graphics are only those loaded at capture time. Tile sheets and maps are reference material; current upstream loader does not automatically replace exploration tiles from them.

## Directory convention

```text
dataset/
  SESSION-0001/
    session.json
    FP-0001/
      state_01.bin
      state_01.txt
      capture_0001/
      capture_metadata.json
```

Use stable IDs. Do not assume memory snapshot counters and graphics capture counters are synchronized; explicitly map filenames in metadata.

## Metadata fields

Record session ID, capture ID, UTC timestamp, local timezone, game/ROM identity as a user-controlled local label (never commit the ROM), upstream repository and commit, app build, platform, scene label, location label, observed character, action, camera state, capture ordering, filenames and verification status.

Use `unknown` rather than guessing. Keep observed labels separate from inferred labels.

## Initial capture matrix

| Group | Capture conditions |
|---|---|
| Exploration | same room stationary; walking; camera scroll; near doorway |
| Dialogue | NPC dialogue; Barry dialogue; Leon dialogue; Lucia dialogue |
| Combat | regular encounter; boss encounter |
| UI | inventory; PDA |
| Transitions | room transition; cutscene |
| Repeatability | save/load; return to a previously captured room |

Aim for at least 16 paired observations initially. This is a target, not a claim that captures exist.

## Fingerprint layers

1. Tile identity: normalized 8×8 pixel patterns, independent of map position.
2. Spatial patch: tile arrangement plus CGB bank, palette, flips and priority attributes.
3. Room identity: stable spatial patches reconciled across camera movement and overlapping views.
4. Scene state: exploration/dialogue/cutscene/battle layered over room identity.

Separate static tiles from animated/dynamic tiles by repeated temporal captures. Do not let animated pixels dominate room matching.

## Integrity and validation

Compute SHA-256 for every raw file. Preserve originals as immutable evidence. Any derived image or normalized representation must record its source capture IDs and transformation version.

No room ID, active character or speaker is considered verified until a proposed signal repeats across multiple captures and is contradicted by appropriate negative controls.

## Implementation references

- [Fingerprint dataset schema](RGM-001E-FINGERPRINT-DATASET.md)
- [Room Fingerprint Engine and candidate matcher](../../tools/ROOM-FINGERPRINT.md)
