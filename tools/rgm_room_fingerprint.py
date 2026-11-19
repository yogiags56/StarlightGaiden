#!/usr/bin/env python3
"""Experimental room-map fingerprinting and camera-shift candidate matching.

This operates on rendered 32x32 RGBA tilemap PNGs. It does not decode raw
VRAM tile IDs/attributes and never assigns a verified in-game room identity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .rgm_graphics_comparator import decode_rgba, ImageError
except ImportError:  # direct execution: python tools/rgm_room_fingerprint.py
    from rgm_graphics_comparator import decode_rgba, ImageError

GRID = 32
TILE_PIXELS = 8


class FingerprintError(Exception):
    """Invalid fingerprint input or incompatible map."""


def extract_cells(path: Path, excluded: set[tuple[int, int]] | None = None) -> dict[str, Any]:
    image = decode_rgba(path)
    if (image["width"], image["height"]) != (GRID*TILE_PIXELS, GRID*TILE_PIXELS):
        raise FingerprintError(f"Expected 256x256 tilemap PNG: {path}")
    excluded = excluded or set()
    pixels = image["pixels"]
    cells: list[str | None] = []
    for ty in range(GRID):
        for tx in range(GRID):
            if (tx, ty) in excluded:
                cells.append(None)
                continue
            tile = bytearray()
            for py in range(TILE_PIXELS):
                start = ((ty*TILE_PIXELS+py)*GRID*TILE_PIXELS+tx*TILE_PIXELS)*4
                tile.extend(pixels[start:start+TILE_PIXELS*4])
            cells.append(hashlib.sha256(tile).hexdigest()[:24])
    usable = [v for v in cells if v is not None]
    counts = Counter(usable)
    # Multiset digest is translation-invariant, but intentionally ignores layout.
    bag = hashlib.sha256("\n".join(sorted(usable)).encode("ascii")).hexdigest()
    return {
        "source": str(path),
        "source_sha256": image["sha256"],
        "grid": f"{GRID}x{GRID}",
        "tile_pixels": f"{TILE_PIXELS}x{TILE_PIXELS}",
        "cells": cells,
        "excluded_cells": len(excluded),
        "usable_cells": len(usable),
        "unique_tile_patterns": len(counts),
        "tile_pattern_counts": dict(sorted(counts.items())),
        "translation_invariant_multiset_sha256": bag,
        "warning": "Rendered RGBA tile patterns only; palette/animation and CGB attributes are already baked into pixels."
    }


def _at(cells: list[str | None], x: int, y: int) -> str | None:
    return cells[(y % GRID)*GRID + (x % GRID)]


def compare_fingerprints(a: dict[str, Any], b: dict[str, Any],
                         max_shift: int = 8, min_overlap: int = 96) -> dict[str, Any]:
    if max_shift < 0 or max_shift > GRID-1:
        raise FingerprintError("max_shift must be between 0 and 31")
    if min_overlap < 1 or min_overlap > GRID*GRID:
        raise FingerprintError("min_overlap must be between 1 and 1024")
    ca, cb = a["cells"], b["cells"]
    best = None
    # Circular shifts model a scrolling tilemap ring buffer. dx/dy are tile cells.
    for dy in range(-max_shift, max_shift+1):
        for dx in range(-max_shift, max_shift+1):
            pairs = []
            for y in range(GRID):
                for x in range(GRID):
                    va, vb = _at(ca, x, y), _at(cb, x+dx, y+dy)
                    if va is not None and vb is not None:
                        pairs.append((va, vb))
            overlap = len(pairs)
            if not overlap:
                continue
            # Inverse-frequency weighting reduces the influence of common floor/wall tiles.
            freq_a, freq_b = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
            total_weight = matched_weight = 0.0
            equal = 0
            for va, vb in pairs:
                weight = 1.0 / ((freq_a[va] * freq_b[vb]) ** 0.5)
                total_weight += weight
                if va == vb:
                    matched_weight += weight
                    equal += 1
            score = matched_weight / total_weight if total_weight else 0.0
            candidate = {"dx_tiles": dx, "dy_tiles": dy, "overlap_cells": overlap,
                         "exact_matching_cells": equal, "weighted_similarity": score}
            if best is None or (score, overlap, equal) > (
                best["weighted_similarity"], best["overlap_cells"], best["exact_matching_cells"]):
                best = candidate
    if best is None:
        return {"status": "insufficient_evidence", "reason": "no comparable static cells"}
    enough = best["overlap_cells"] >= min_overlap
    # These are provisional engineering gates, not empirically calibrated thresholds.
    status = "candidate_match" if enough and best["weighted_similarity"] >= 0.82 else (
        "weak_candidate" if enough and best["weighted_similarity"] >= 0.60 else "insufficient_evidence")
    return {
        "status": status,
        "best_alignment": best,
        "minimum_overlap_required": min_overlap,
        "overlap_sufficient": enough,
        "thresholds": {"candidate_match": 0.82, "weak_candidate": 0.60,
                       "calibration": "provisional; requires real-game captures"},
        "interpretation": "Candidate similarity only. Never treat this as a verified room ID.",
        "comparison": {"source_a": a["source"], "source_b": b["source"],
                       "multiset_digest_equal": a["translation_invariant_multiset_sha256"] ==
                                               b["translation_invariant_multiset_sha256"]}
    }


def load_exclusions(path: Path | None) -> set[tuple[int, int]]:
    if path is None:
        return set()
    raw = json.loads(path.read_text(encoding="utf-8"))
    values = raw.get("exclude_cells", [])
    result = set()
    for item in values:
        if not isinstance(item, list) or len(item) != 2:
            raise FingerprintError("exclude_cells entries must be [x, y]")
        x, y = item
        if not isinstance(x, int) or not isinstance(y, int) or not (0 <= x < GRID and 0 <= y < GRID):
            raise FingerprintError(f"invalid excluded tile coordinate: {item}")
        result.add((x, y))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map_a", type=Path)
    parser.add_argument("map_b", type=Path, nargs="?")
    parser.add_argument("--exclude-a", type=Path, help="JSON with exclude_cells [[x,y], ...]")
    parser.add_argument("--exclude-b", type=Path)
    parser.add_argument("--max-shift", type=int, default=8)
    parser.add_argument("--min-overlap", type=int, default=96)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        a = extract_cells(args.map_a, load_exclusions(args.exclude_a))
        report: dict[str, Any] = {"schema_version": 1, "tool": "RGM Room Fingerprint",
                                  "fingerprint_a": {k:v for k,v in a.items() if k != "cells"}}
        if args.map_b:
            b = extract_cells(args.map_b, load_exclusions(args.exclude_b))
            report["fingerprint_b"] = {k:v for k,v in b.items() if k != "cells"}
            report["match"] = compare_fingerprints(a, b, args.max_shift, args.min_overlap)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(payload+"\n", encoding="utf-8")
            print(f"Report written: {args.output}")
        else:
            print(payload)
        return 0
    except (OSError, ValueError, KeyError, ImageError, FingerprintError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
