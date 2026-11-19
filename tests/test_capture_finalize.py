import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.rgm_capture_finalize import finalize_capture,FinalizeError

class CaptureFinalizeTests(unittest.TestCase):
 def make_bundle(self,root):
  d=root/"FP-001";g=d/"capture_0001";g.mkdir(parents=True)
  (d/"state_01.bin").write_bytes(b"state")
  (d/"state_01.txt").write_text("summary")
  for name in ("framebuffer.png","map_9800.png","map_9c00.png","manifest.txt"):
   (g/name).write_bytes(("fixture:"+name).encode())
  meta={"schema_version":1,"capture_id":"FP-001","capture":{"state_file":"state_01.bin","state_summary":"state_01.txt","graphics_directory":"capture_0001"},"source_sha256":{}}
  (d/"capture_metadata.json").write_text(json.dumps(meta))
  return d
 def test_finalize_hashes_all_artifacts(self):
  with tempfile.TemporaryDirectory() as td:
   d=self.make_bundle(Path(td));r=finalize_capture(d)
   m=json.loads((d/"capture_metadata.json").read_text())
   self.assertEqual(r["status"],"finalized")
   self.assertEqual(r["artifact_count"],6)
   self.assertEqual(m["source_sha256"]["state_01.bin"],hashlib.sha256(b"state").hexdigest())
 def test_missing_required_graphic_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   d=self.make_bundle(Path(td));(d/"capture_0001"/"map_9800.png").unlink()
   with self.assertRaises(FinalizeError):finalize_capture(d)
 def test_path_escape_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);d=self.make_bundle(root);m=json.loads((d/"capture_metadata.json").read_text())
   m["capture"]["state_file"]="../outside.bin";(d/"capture_metadata.json").write_text(json.dumps(m))
   (root/"outside.bin").write_bytes(b"outside")
   with self.assertRaises(FinalizeError):finalize_capture(d)
 def test_symlink_state_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);d=self.make_bundle(root);(d/"state_01.bin").unlink()
   target=root/"external.bin";target.write_bytes(b"external");(d/"state_01.bin").symlink_to(target)
   with self.assertRaises(FinalizeError):finalize_capture(d)

if __name__=="__main__":unittest.main()
