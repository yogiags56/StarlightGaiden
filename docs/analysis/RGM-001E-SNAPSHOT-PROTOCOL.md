# Room Fingerprint Dataset Schema

Each observation should preserve the raw paired state/graphics captures and a derived fingerprint report.

```text
dataset/
  SESSION-0001/
    FP-0001/
      state.bin
      state.txt
      graphics/
        map_9800.png
        map_9c00.png
        framebuffer.png
        manifest.txt
      capture_metadata.json
      derived/
        map_9800.fingerprint.json
        map_9800.match.json
```

Metadata must distinguish:
- `observed.location_label`: label entered by the tester, not inferred by software.
- `observed.character` and `observed.activity`: direct observation.
- `inferred.room_candidate`: tool output, initially null.
- `verification.status`: `unverified`, `provisional`, or `verified`.
- `source.sha256`: checksums of every raw source file.
- `tool.version` and `tool.commit`: exact analyzer provenance.

A room candidate can only become verified after repeat captures from the same physical room, negative controls from other rooms, camera-scroll tests, and dynamic/palette variation tests have been evaluated.
