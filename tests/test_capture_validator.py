import hashlib,json,struct,tempfile,unittest,zlib
from pathlib import Path
from tools.rgm_capture_validator import inspect_capture,run_dataset
from tools.rgm_snapshot_analyzer import MAGIC,EXPECTED
SIG=b"\\x89PNG\\r\\n\\x1a\\n"
def chunk(k,d): return struct.pack(">I",len(d))+k+d+struct.pack(">I",zlib.crc32(k+d)&0xffffffff)
def png(p,w,h,pix):
 raw=b"".join(b"\\0"+pix[y*w*4:(y+1)*w*4] for y in range(h)); ih=struct.pack(">IIBBBBB",w,h,8,6,0,0,0)
 p.write_bytes(SIG+chunk(b"IHDR",ih)+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b""))
def snapshot(p): p.write_bytes(MAGIC+struct.pack("<4I",*EXPECTED.values())+b"".join(bytes([i])*n for i,n in enumerate(EXPECTED.values())))
def capture(root,cid,label,bad=False):
 d=root/"SESSION-0001"/cid; g=d/"graphics"; g.mkdir(parents=True); s=d/"state.bin"; snapshot(s); t=d/"state.txt"; t.write_text("ROM_BANK=1\\n")
 pix=bytearray()
 for y in range(256):
  for x in range(256):
   v=((x//8)*17+(y//8)*31)%251; pix.extend((v,v*3%256,v*7%256,255))
 png(g/"map_9800.png",256,256,pix); png(g/"map_9c00.png",256,256,pix); png(g/"framebuffer.png",160,144,bytes([1,2,3,255]*(160*144)))
 (g/"manifest.txt").write_text("SCX=0\\n")
 checks={str(p.relative_to(d)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (s,t,*g.iterdir())}
 if bad: checks["state.bin"]="0"*64
 meta={"schema_version":1,"session_id":"SESSION-0001","capture_id":cid,"observed":{"location_label":label,"activity":"exploration"},
 "capture":{"state_file":"state.bin","state_summary":"state.txt","graphics_directory":"graphics"},"source_sha256":checks}
 (d/"capture_metadata.json").write_text(json.dumps(meta)); return d
class Tests(unittest.TestCase):
 def test_valid_and_pairs(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td); capture(r,"FP-1","Corridor"); capture(r,"FP-2","Corridor"); capture(r,"FP-3","Engine")
   x=run_dataset(r,0,900); self.assertEqual(x["summary"]["captures_valid"],3, x["capture_checks"]); self.assertEqual(x["summary"]["pair_trials"],3)
   self.assertEqual(x["summary"]["same_label_pairs"],1); self.assertEqual(x["summary"]["different_label_pairs"],2)
 def test_bad_checksum(self):
  with tempfile.TemporaryDirectory() as td:
   d=capture(Path(td),"FP-1","Corridor",True); x=inspect_capture(d)
   self.assertEqual(x["status"],"invalid"); self.assertTrue(any("SHA-256 mismatch" in e for e in x["errors"]))
 def test_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   d=capture(Path(td),"FP-1","Corridor"); p=d/"capture_metadata.json"; m=json.loads(p.read_text()); m["capture"]["state_file"]="../outside"; p.write_text(json.dumps(m))
   x=inspect_capture(d); self.assertEqual(x["status"],"invalid"); self.assertTrue(any("escapes" in e for e in x["errors"]))
if __name__=="__main__": unittest.main()
