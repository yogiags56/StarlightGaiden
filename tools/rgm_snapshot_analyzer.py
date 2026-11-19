#!/usr/bin/env python3
"""Offline analyzer for Resident Evil Gaiden recomp guest snapshots.

Reads the upstream REGAIDEN-SNAPSHOT-1 binary container and optional text
summary. It never modifies input files. Python standard library only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

MAGIC = b"REGAIDEN-SNAPSHOT-1\\0"
EXPECTED = {"wram": 0x8000, "hram": 0x7F, "io": 0x80, "oam": 0xA0}


class SnapshotError(Exception):
    """Invalid or unsupported snapshot input."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_snapshot(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if not raw.startswith(MAGIC):
        raise SnapshotError(f"{path}: magic/header tidak cocok")
    offset = len(MAGIC)
    size_bytes = raw[offset:offset + 16]
    if len(size_bytes) != 16:
        raise SnapshotError(f"{path}: tabel ukuran terpotong")
    candidates = []
    for endian in ("<", ">"):
        sizes = struct.unpack(endian + "4I", size_bytes)
        if tuple(sizes) == tuple(EXPECTED.values()):
            candidates.append((endian, sizes))
    if len(candidates) != 1:
        raise SnapshotError(f"{path}: ukuran blok tidak dikenal")
    endian, sizes = candidates[0]
    offset += 16
    names = ("wram", "hram", "io", "oam")
    blocks = {}
    for name, size in zip(names, sizes):
        end = offset + size
        if end > len(raw):
            raise SnapshotError(f"{path}: blok {name} terpotong")
        blocks[name] = raw[offset:end]
        offset = end
    if offset != len(raw):
        raise SnapshotError(f"{path}: ada {len(raw) - offset} byte tambahan setelah OAM")
    return {"path": str(path), "sha256": sha256(raw), "blocks": blocks,
            "sizes": dict(zip(names, sizes)), "endian": "little" if endian == "<" else "big"}


def parse_summary(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def ranges(indices: list[int]) -> list[dict[str, int]]:
    if not indices:
        return []
    out = []
    start = previous = indices[0]
    for index in indices[1:]:
        if index != previous + 1:
            out.append({"start": start, "end": previous, "length": previous - start + 1})
            start = index
        previous = index
    out.append({"start": start, "end": previous, "length": previous - start + 1})
    return out


def changed_bytes(a: bytes, b: bytes) -> dict[str, Any]:
    if len(a) != len(b):
        raise SnapshotError("ukuran blok berbeda")
    indices = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    return {"changed_count": len(indices), "total": len(a),
            "ratio": len(indices) / len(a) if a else 0.0,
            "first_offsets_hex": [f"0x{i:04X}" for i in indices[:32]],
            "changed_ranges": ranges(indices)}


def compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    result = {"snapshot_a": a["path"], "snapshot_b": b["path"],
              "sha256_a": a["sha256"], "sha256_b": b["sha256"], "blocks": {}}
    for name in ("wram", "hram", "io", "oam"):
        result["blocks"][name] = changed_bytes(a["blocks"][name], b["blocks"][name])
    banks = []
    for bank in range(8):
        start = bank * 0x1000
        count = sum(x != y for x, y in zip(
            a["blocks"]["wram"][start:start + 0x1000],
            b["blocks"]["wram"][start:start + 0x1000]))
        banks.append({"bank": bank, "changed_bytes": count, "total": 0x1000})
    result["wram_bank_changes"] = banks
    result["summary"] = {
        "changed_wram_bytes": result["blocks"]["wram"]["changed_count"],
        "changed_hram_bytes": result["blocks"]["hram"]["changed_count"],
        "changed_io_bytes": result["blocks"]["io"]["changed_count"],
        "changed_oam_bytes": result["blocks"]["oam"]["changed_count"]}
    return result


def png_info(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\\x89PNG\\r\\n\\x1a\\n" or data[12:16] != b"IHDR":
        raise SnapshotError(f"PNG tidak valid: {path}")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29])
    return {"file": str(path), "sha256": sha256(data), "width": width, "height": height,
            "bit_depth": depth, "color_type": color_type, "interlace": interlace,
            "bytes": len(data)}


def inspect_graphics(directory: Path | None) -> dict[str, Any]:
    if directory is None:
        return {}
    if not directory.is_dir():
        raise SnapshotError(f"Direktori graphics tidak ditemukan: {directory}")
    files = sorted(directory.glob("*.png"))
    return {"directory": str(directory), "png_count": len(files),
            "files": [png_info(path) for path in files],
            "manifest_present": (directory / "manifest.txt").exists()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_a", type=Path)
    parser.add_argument("snapshot_b", type=Path, nargs="?")
    parser.add_argument("--summary-a", type=Path)
    parser.add_argument("--summary-b", type=Path)
    parser.add_argument("--graphics-a", type=Path)
    parser.add_argument("--graphics-b", type=Path)
    parser.add_argument("--output", type=Path, help="JSON output path; stdout if omitted")
    args = parser.parse_args()
    try:
        a = parse_snapshot(args.snapshot_a)
        report: dict[str, Any] = {
            "schema_version": 1, "analyzer": "RGM Snapshot Analyzer",
            "snapshot_a": {"path": a["path"], "sha256": a["sha256"],
                           "sizes": a["sizes"], "endian": a["endian"],
                           "summary": parse_summary(args.summary_a)},
            "graphics_a": inspect_graphics(args.graphics_a)}
        if args.snapshot_b:
            b = parse_snapshot(args.snapshot_b)
            report["snapshot_b"] = {
                "path": b["path"], "sha256": b["sha256"], "sizes": b["sizes"],
                "endian": b["endian"], "summary": parse_summary(args.summary_b)}
            report["comparison"] = compare(a, b)
            report["graphics_b"] = inspect_graphics(args.graphics_b)
        payload = json.dumps(report, indent=2, ensure_ascii=False)
        if args.output:
            args.output.write_text(payload + "\\n", encoding="utf-8")
            print(f"Report ditulis: {args.output}")
        else:
            print(payload)
        return 0
    except (OSError, SnapshotError, ValueError, struct.error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
