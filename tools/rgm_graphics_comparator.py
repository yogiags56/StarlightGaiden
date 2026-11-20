#!/usr/bin/env python3
"""Compare RGBA PNG exports from the Resident Evil Gaiden asset dumper."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

SIG = b"\x89PNG\r\n\x1a\n"
MAP_W = MAP_H = 256
TILE = 8


class ImageError(Exception):
    pass


def decode_rgba(path: Path):
    data = path.read_bytes()
    if not data.startswith(SIG):
        raise ImageError(f"Invalid PNG signature: {path}")
    pos, width, height, depth, color, interlace = 8, None, None, None, None, None
    compressed = bytearray()
    ended = False
    while pos + 12 <= len(data):
        size = struct.unpack(">I", data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        end = pos + 12 + size
        if end > len(data):
            raise ImageError(f"Truncated PNG chunk: {path}")
        payload = data[pos+8:pos+8+size]
        crc = struct.unpack(">I", data[pos+8+size:end])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ImageError(f"PNG CRC mismatch: {path}")
        if kind == b"IHDR":
            if size != 13 or width is not None:
                raise ImageError(f"Invalid IHDR: {path}")
            width, height, depth, color, comp, filt, interlace = struct.unpack(">IIBBBBB", payload)
            if comp or filt:
                raise ImageError(f"Unsupported PNG compression/filter method: {path}")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            ended = True
            pos = end
            break
        pos = end
    if not ended or width is None or not compressed:
        raise ImageError(f"Incomplete PNG: {path}")
    if depth != 8 or color != 6 or interlace != 0:
        raise ImageError(f"Expected 8-bit RGBA non-interlaced PNG: {path}")
    if width < 1 or height < 1 or width * height > 100_000_000:
        raise ImageError(f"Invalid PNG dimensions: {path}")
    stride, bpp = width * 4, 4
    try:
        raw = zlib.decompress(compressed)
    except zlib.error as exc:
        raise ImageError(f"PNG IDAT decompression failed: {path}: {exc}") from exc
    if len(raw) != (stride + 1) * height:
        raise ImageError(f"Unexpected PNG pixel-data length: {path}")
    pixels = bytearray(stride * height)
    src = 0
    for y in range(height):
        ft = raw[src]
        src += 1
        row, prev = y * stride, (y - 1) * stride
        for x in range(stride):
            v = raw[src]
            src += 1
            left = pixels[row+x-bpp] if x >= bpp else 0
            up = pixels[prev+x] if y else 0
            ul = pixels[prev+x-bpp] if y and x >= bpp else 0
            if ft == 1:
                v = (v + left) & 255
            elif ft == 2:
                v = (v + up) & 255
            elif ft == 3:
                v = (v + (left + up)//2) & 255
            elif ft == 4:
                p = left + up - ul
                pa, pb, pc = abs(p-left), abs(p-up), abs(p-ul)
                predictor = left if pa <= pb and pa <= pc else (up if pb <= pc else ul)
                v = (v + predictor) & 255
            elif ft != 0:
                raise ImageError(f"Unknown PNG filter {ft}: {path}")
            pixels[row+x] = v
    return {"width": width, "height": height, "pixels": bytes(pixels),
            "sha256": hashlib.sha256(data).hexdigest()}


def pixel_diff(a, b):
    if (a["width"], a["height"]) != (b["width"], b["height"]):
        raise ImageError("Image dimensions differ; no implicit resizing is performed")
    w, h, pa, pb = a["width"], a["height"], a["pixels"], b["pixels"]
    count, minx, miny, maxx, maxy = 0, w, h, -1, -1
    for y in range(h):
        row = y*w*4
        for x in range(w):
            i = row+x*4
            if pa[i:i+4] != pb[i:i+4]:
                count += 1
                minx, miny, maxx, maxy = min(minx,x), min(miny,y), max(maxx,x), max(maxy,y)
    total = w*h
    return {"width": w, "height": h, "changed_pixels": count, "total_pixels": total,
            "changed_ratio": count/total, "bounding_box": None if not count else
            {"x":minx,"y":miny,"width":maxx-minx+1,"height":maxy-miny+1}}


def regions(cells):
    todo, output = set(cells), []
    while todo:
        seed = todo.pop()
        stack, part = [seed], [seed]
        while stack:
            x,y = stack.pop()
            for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if n in todo:
                    todo.remove(n)
                    stack.append(n)
                    part.append(n)
        xs, ys = [p[0] for p in part], [p[1] for p in part]
        output.append({"tile_count":len(part),"tile_x":min(xs),"tile_y":min(ys),
                       "tile_width":max(xs)-min(xs)+1,"tile_height":max(ys)-min(ys)+1})
    return sorted(output,key=lambda r:(-r["tile_count"],r["tile_y"],r["tile_x"]))


def compare_tilemaps(path_a: Path, path_b: Path):
    a,b = decode_rgba(path_a),decode_rgba(path_b)
    if (a["width"],a["height"]) != (MAP_W,MAP_H) or (b["width"],b["height"]) != (MAP_W,MAP_H):
        raise ImageError("Tilemaps must be 256x256 pixels: 32x32 cells of 8x8 pixels")
    cells, coords, changed_pixels = [], set(), 0
    for ty in range(32):
        for tx in range(32):
            n = 0
            for py in range(8):
                start = ((ty*8+py)*256+tx*8)*4
                for px in range(8):
                    i = start+px*4
                    n += a["pixels"][i:i+4] != b["pixels"][i:i+4]
            if n:
                cells.append({"x":tx,"y":ty,"changed_pixels":n,"tile_pixel_ratio":n/64})
                coords.add((tx,ty))
                changed_pixels += n
    return {"image_a":str(path_a),"image_b":str(path_b),"tile_grid":"32x32","tile_size":"8x8",
            "changed_tiles":len(cells),"total_tiles":1024,"changed_tile_ratio":len(cells)/1024,
            "changed_pixels_in_tiles":changed_pixels,"changed_cells":cells,
            "contiguous_regions_4way":regions(coords),
            "note":"Visual RGBA comparison; not a raw VRAM tile-index/attribute comparison."}


def compare_dirs(a: Path, b: Path):
    if not a.is_dir() or not b.is_dir():
        raise ImageError("Both graphics capture directories must exist")
    report = {"directory_a":str(a),"directory_b":str(b),"tilemaps":{},"framebuffer":None,"tile_sheets":{}}
    for name in ("map_9800.png","map_9c00.png"):
        x,y = a/name,b/name
        report["tilemaps"][name] = compare_tilemaps(x,y) if x.exists() and y.exists() else {"status":"missing"}
    x,y = a/"framebuffer.png",b/"framebuffer.png"
    report["framebuffer"] = pixel_diff(decode_rgba(x),decode_rgba(y)) if x.exists() and y.exists() else {"status":"missing"}
    names = {p.name for p in a.glob("tiles_*.png")} | {p.name for p in b.glob("tiles_*.png")}
    for name in sorted(names):
        x,y = a/name,b/name
        report["tile_sheets"][name] = pixel_diff(decode_rgba(x),decode_rgba(y)) if x.exists() and y.exists() else {"status":"missing_in_one_capture"}
    report["interpretation_warning"] = (
        "Palette/animation changes can alter rendered pixels without changing room identity. "
        "Correlate repeated captures, camera metadata and memory snapshots; do not infer room_id from one diff.")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture_a", type=Path)
    p.add_argument("capture_b", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = compare_dirs(args.capture_a,args.capture_b)
        text = json.dumps({"schema_version":1,"tool":"RGM Graphics Comparator","comparison":result},
                          indent=2,ensure_ascii=False)
        if args.output:
            args.output.write_text(text+"\n",encoding="utf-8")
            print(f"Report written: {args.output}")
        else:
            print(text)
        return 0
    except (OSError,ImageError,ValueError,struct.error) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
