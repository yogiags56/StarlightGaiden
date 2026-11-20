import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from tools.rgm_graphics_comparator import decode_rgba, compare_tilemaps, pixel_diff

SIG=b"\x89PNG\r\n\x1a\n"
def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data)&0xffffffff)
def write_png(path,w,h,pixels):
    raw=b"".join(b"\0"+pixels[y*w*4:(y+1)*w*4] for y in range(h))
    ihdr=struct.pack(">IIBBBBB",w,h,8,6,0,0,0)
    path.write_bytes(SIG+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b""))

class ComparatorTests(unittest.TestCase):
    def test_png_decode(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"test.png"; pixels=bytes([1,2,3,255])
            write_png(p,1,1,pixels)
            self.assertEqual(decode_rgba(p)["pixels"],pixels)
    def test_tilemap_cells_and_regions(self):
        with tempfile.TemporaryDirectory() as d:
            a,b=Path(d)/"a.png",Path(d)/"b.png"
            base=bytearray([0,0,0,255]*(256*256)); changed=bytearray(base)
            for ty,tx in ((3,2),(3,3)):
                for y in range(ty*8,ty*8+8):
                    for x in range(tx*8,tx*8+8):
                        i=(y*256+x)*4; changed[i:i+4]=bytes([255,0,0,255])
            write_png(a,256,256,base); write_png(b,256,256,changed)
            report=compare_tilemaps(a,b)
            self.assertEqual(report["changed_tiles"],2)
            self.assertEqual(report["changed_pixels_in_tiles"],128)
            self.assertEqual(report["contiguous_regions_4way"][0]["tile_count"],2)
    def test_pixel_diff_bbox(self):
        a={"width":2,"height":2,"pixels":bytes([0,0,0,255]*4)}
        p=bytearray(a["pixels"]); p[4:8]=bytes([1,2,3,255])
        b={"width":2,"height":2,"pixels":bytes(p)}
        self.assertEqual(pixel_diff(a,b)["bounding_box"],{"x":1,"y":0,"width":1,"height":1})

if __name__=="__main__":
    unittest.main()
