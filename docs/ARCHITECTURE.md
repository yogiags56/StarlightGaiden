# Architecture and Source Provenance

## Product architecture

- **Android shell:** application lifecycle, storage access, display and input.
- **Runtime/recompilation layer:** upstream Game Boy execution and compatibility.
- **Presentation layer:** original-faithful gameplay with remastered 2D assets.
- **Exploration renderer:** future tilemap/scene-aware presentation; not yet implemented.
- **Combat renderer:** existing upstream HD hooks are the initial reference; state selection needs validation.
- **Asset pipeline:** manifests, image validation, scene fingerprints and provenance.
- **Analysis tools:** offline snapshot parser, graphics comparator and dataset reports.

## Upstream boundary

Current candidate: [regaiden-recomp](https://github.com/sergiomanzur/regaiden-recomp).

Baseline source commit inspected: `e5befd20e67939d939319149d1c1177b8e6c5cd6`.

This repository does not claim to contain a complete upstream checkout. Upstream code must be brought in through a documented, license-compliant integration decision. Track imported source separately and preserve attribution and license notices.

## Evidence rules

- A design proposal is not an implementation.
- A synthetic test is not a game-runtime test.
- A source audit is not a successful build.
- A byte correlation is not a semantic state identifier until reproduced across multiple captures.
- ROM addresses and WRAM offsets must always state their bank/window context.
- Music track, PC, ROM bank, HP values and camera registers are supporting signals, not standalone room or character identifiers.

## Key unresolved detection risks

1. Existing battle background/monster rendering still uses a `WRAM $C900` heuristic; this is not accepted as a validated battle flag.
2. UI detection uses WRAM bank selection; intro/cutscene classification needs real capture validation.
3. HP bytes for Barry, Leon and Lucia do not prove which character is active or speaking.
4. Existing upstream HD replacements cover battle backgrounds, monsters and dialogue portraits, not arbitrary exploration tilemap replacement.
5. Tilemap memory is a scrolling/ring-buffer view; hashing the entire raw tilemap or VRAM as a room ID is invalid.

## Target constraints

- Android ARM64-v8a is primary.
- Preserve original game logic and story.
- Preserve aspect ratio and avoid stretching.
- Keep source, docs, manifests, tests, logs and reproducible build instructions in this repository.
