# Changelog

## Unreleased — RGM-001E.4 Graphics Comparator

- Added a standard-library RGBA PNG decoder for upstream asset-dump output.
- Added pixel-level framebuffer and tile-sheet comparison.
- Added 32×32 tilemap cell comparison and 4-way contiguous change regions.
- Added CRC checks, malformed PNG validation and synthetic comparator tests.
- Explicitly documents that visual tilemap diffs are not raw VRAM tile-index comparisons and cannot independently identify rooms.

## RGM-001E.3 repository bootstrap

- Initialized the StarlightGaiden project repository.
- Added project direction, roadmap, architecture/provenance and snapshot protocol.
- Integrated the offline snapshot analyzer prototype.
- Added synthetic unit tests; real game captures and Android runtime validation remain pending.
