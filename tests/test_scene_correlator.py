import hashlib,json,struct,tempfile,unittest,zlib
from pathlib import Path
from tools.rgm_scene_correlator import run_dataset,parse_summary
from tools.rgm_snapshot_analyzer import MAGIC,EXPECTED
SIG=b"\\x89PNG\\r\\n\\x1a\\n"
def ch(k,d):return struct.pack(">I",len(d))+k+d+struct.pack(">I",zlib.crc32(k+d)&0xffffffff)
def png(p,w,h,pix):
 raw=b"".join(b"\\0"+pix[y*w*4:(y+1)*w*4] for y in range(h));p.write_bytes(SIG+ch(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+ch(b"IDAT",zlib.compress(raw))+ch(b"IEND",b""))
def make(root,cid,label):
 d=root/"SESSION-1"/cid;g=d/"graphics";g.mkdir(parents=True);s=d/"state.bin"
 wr=bytearray(0x8000);wr[0xe8c]=1
 s.write_bytes(MAGIC+struct.pack("<4I",*EXPECTED.values())+bytes(wr)+bytes(0x7f)+bytes(0x80)+bytes(0xa0))
 t=d/"state.txt";t.write_text(f"label={label}\nrom_bank=1\nwram_bank=1\npc=1234 sp=FFFE\nLCDC(FF40)=91 STAT(FF41)=00\nSCY(FF42)=00 SCX(FF43)=00 LY(FF44)=00\nWY(FF4A)=90 WX(FF4B)=07\nobj00 y= 32 x= 40 tile=02 flags=00\nactive_sprite_count=1\n")
 pix=bytearray()
 for y in range(256):
  for x in range(256):
   v=((x//8)*17+(y//8)*31)%251;pix.extend((v,v*3%256,v*7%256,255))
 png(g/"map_9800.png",256,256,pix);png(g/"map_9c00.png",256,256,pix);png(g/"framebuffer.png",160,144,bytes([1,2,3,255]*(160*144)));(g/"manifest.txt").write_text("SCX=0\n")
 checks={str(q.relative_to(d)):hashlib.sha256(q.read_bytes()).hexdigest() for q in (s,t,*g.iterdir())}
 (d/"capture_metadata.json").write_text(json.dumps({"schema_version":1,"session_id":"SESSION-1","capture_id":cid,"observed":{"location_label":label,"activity":"exploration"},"capture":{"state_file":"state.bin","state_summary":"state.txt","graphics_directory":"graphics"},"source_sha256":checks}))
class Tests(unittest.TestCase):
 def test_pair_correlation(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);make(r,"FP-1","Corridor");make(r,"FP-2","Corridor")
   q=run_dataset(r,0,900);self.assertEqual(q["summary"]["pair_correlations"],1)
   p=q["pair_correlations"][0];self.assertEqual(p["status"],"strong_correlation_candidate")
   self.assertIn("same_rom_bank",p["corroborating_signals"])
   self.assertIn("memory_transition",p)
 def test_parse_real_upstream_summary(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"s";p.write_text("label=Test\nrom_bank=13\nwram_bank=2\npc=ABCD sp=FFFE\nLCDC(FF40)=91 STAT(FF41)=00\nSCY(FF42)=12 SCX(FF43)=34 LY(FF44)=56\nWY(FF4A)=90 WX(FF4B)=07\nobj00 y= 32 x= 40 tile=02 flags=00\nactive_sprite_count=1\n")
   x=parse_summary(p);self.assertEqual(x["rom_bank"],13);self.assertEqual(x["pc"],0xABCD);self.assertEqual(x["scx"],0x34);self.assertEqual(len(x["active_sprites"]),1)
if __name__=="__main__":unittest.main()
