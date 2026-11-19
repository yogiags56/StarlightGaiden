import hashlib,json,struct,tempfile,unittest,zlib
from pathlib import Path
from tools.rgm_scene_classifier import analyze_capture
from tools.rgm_snapshot_analyzer import MAGIC,EXPECTED
SIG=b"\\x89PNG\\r\\n\\x1a\\n"
def ch(k,d):return struct.pack(">I",len(d))+k+d+struct.pack(">I",zlib.crc32(k+d)&0xffffffff)
def png(p,w,h,pix):
 raw=b"".join(b"\\0"+pix[y*w*4:(y+1)*w*4] for y in range(h))
 p.write_bytes(SIG+ch(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+ch(b"IDAT",zlib.compress(raw))+ch(b"IEND",b""))
def capture(root,cid,bank=1,lcdc=0x91,wy=0,wx=7):
 d=root/"SESSION-1"/cid;g=d/"graphics";g.mkdir(parents=True)
 wr=bytearray(0x8000);wr[0xe8c]=10
 s=d/"state.bin";s.write_bytes(MAGIC+struct.pack("<4I",*EXPECTED.values())+bytes(wr)+bytes(0x7f)+bytes(0x80)+bytes(0xa0))
 t=d/"state.txt";t.write_text(f"label={cid}\\nrom_bank=13\\nwram_bank={bank}\\npc=1234 sp=FFFE\\nLCDC(FF40)={lcdc:02X} STAT(FF41)=00\\nSCY(FF42)=00 SCX(FF43)=00 LY(FF44)=00\\nWY(FF4A)={wy:02X} WX(FF4B)={wx:02X}\\nactive_sprite_count=0\\n")
 px=bytes([1,2,3,255])*(256*256)
 png(g/"map_9800.png",256,256,px);png(g/"map_9c00.png",256,256,px);png(g/"framebuffer.png",160,144,bytes([1,2,3,255])*(160*144));(g/"manifest.txt").write_text("SCX=0\\n")
 files=(s,t,*g.iterdir());checks={str(x.relative_to(d)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files}
 m={"schema_version":1,"session_id":"SESSION-1","capture_id":cid,"observed":{"location_label":"test","activity":"test"},"capture":{"state_file":"state.bin","state_summary":"state.txt","graphics_directory":"graphics"},"source_sha256":checks}
 (d/"capture_metadata.json").write_text(json.dumps(m));return d
class SceneClassifierTests(unittest.TestCase):
 def test_ui_bank_is_only_ui_family_not_inventory_assertion(self):
  with tempfile.TemporaryDirectory() as td:
   r=analyze_capture(capture(Path(td),"FP-UI",bank=2))
   c=r["candidates"][0];self.assertEqual(c["type"],"ui_screen_family")
   self.assertEqual(c["subtype"],"unresolved")
   self.assertIn("inventory",c["cannot_distinguish"])
 def test_dialogue_geometry_candidate(self):
  with tempfile.TemporaryDirectory() as td:
   r=analyze_capture(capture(Path(td),"FP-DIALOG",bank=1,lcdc=0xB1,wy=90,wx=7))
   self.assertEqual(r["candidates"][0]["type"],"dialogue")
   self.assertEqual(r["identity"]["speaker"],"unknown")
 def test_no_false_exploration_or_combat_classification(self):
  with tempfile.TemporaryDirectory() as td:
   r=analyze_capture(capture(Path(td),"FP-UNKNOWN",bank=1,lcdc=0x91,wy=0))
   self.assertEqual(r["candidates"][0]["type"],"unclassified")
   self.assertEqual(r["scene_type_states"]["normal_combat"],"unresolved")
   self.assertEqual(r["scene_type_states"]["exploration"],"unresolved")
if __name__=="__main__":unittest.main()
