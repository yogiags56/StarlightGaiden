import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from tools.rgm_room_fingerprint import extract_cells, compare_fingerprints
SIG=b"\x89PNG\r\n\x1a\n"
def chunk(k,d):
    return struct.pack(">I",len(d))+k+d+struct.pack(">I",zlib.crc32(k+d)&0xffffffff)
def write_png(path,w,h,pixels):
    raw=b"".join(b"\0"+pixels[y*w*4:(y+1)*w*4] for y in range(h))
    ihdr=struct.pack(">IIBBBBB",w,h,8,6,0,0,0)
    path.write_bytes(SIG+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b""))
def shift_map(pixels,dx,dy):
    out=bytearray(len(pixels))
    for y in range(32):
        for x in range(32):
            sx=(x-dx)%32; sy=(y-dy)%32
            src=(sy*8*256+sx*8)*4
            dst=(y*8*256+x*8)*4
            for py in range(8):
                out[dst+py*256*4:dst+py*256*4+8*4]=pixels[src+py*256*4:src+py*256*4+8*4]
    return out
class RoomFingerprintTests(unittest.TestCase):
    def test_translation_shift_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.png"; q=Path(d)/"b.png"
            base=bytearray()
            for y in range(256):
                for x in range(256):
                    tile=((x//8)*17+(y//8)*31)%251
                    base.extend((tile,(tile*3)%256,(tile*7)%256,255))
            moved=shift_map(base,3,-2)
            write_png(p,256,256,base); write_png(q,256,256,moved)
            a,b=extract_cells(p),extract_cells(q)
            result=compare_fingerprints(a,b,max_shift=4,min_overlap=900)
            self.assertEqual(result["status"],"candidate_match")
            self.assertEqual((result["best_alignment"]["dx_tiles"],result["best_alignment"]["dy_tiles"]),(3,-2))
            self.assertEqual(result["best_alignment"]["exact_matching_cells"],1024)
    def test_excluded_cells_reduce_overlap(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.png"; q=Path(d)/"b.png"
            pixels=bytes([12,34,56,255]*(256*256))
            write_png(p,256,256,pixels); write_png(q,256,256,pixels)
            excluded={(x,y) for y in range(32) for x in range(32) if x<30}
            a,b=extract_cells(p,excluded),extract_cells(q,excluded)
            result=compare_fingerprints(a,b,max_shift=0,min_overlap=96)
            self.assertEqual(result["status"],"insufficient_evidence")
            self.assertEqual(result["best_alignment"]["overlap_cells"],64)
    def test_identical_map(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"a.png"
            pixels=bytes([20,40,60,255]*(256*256))
            write_png(p,256,256,pixels)
            a=extract_cells(p)
            result=compare_fingerprints(a,a,max_shift=0,min_overlap=900)
            self.assertEqual(result["status"],"candidate_match")
            self.assertEqual(result["best_alignment"]["weighted_similarity"],1.0)
if __name__=="__main__":
    unittest.main()
