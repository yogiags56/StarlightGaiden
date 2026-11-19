import json,shutil,tempfile,unittest
from pathlib import Path
from tools.rgm_collection_status import audit_session,CollectionError
from tools.rgm_experiment_plan import generate
from tests.test_capture_validator import capture

def matrix():
 return {"schema_version":1,"milestone":"RGM-001E.9","project":"Test","upstream":{"repository":"x","commit":"abc"},
 "protocol":{"repeat_count":1},"experiments":[{"id":"EXP-01","name":"Test","target":"exploration","sequence":["before"],"captures":["before","after"],"question":"Q?"}]}

class CollectionStatusTests(unittest.TestCase):
 def create_plan(self,root):
  m=root/"matrix.json";m.write_text(json.dumps(matrix()))
  out=root/"SESSION-0001";generate(m,out,"SESSION-0001");return out
 def test_blank_plan_is_reported_as_planned(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.create_plan(Path(td));r=audit_session(session)
   self.assertEqual(r["summary"]["planned_captures"],2)
   self.assertEqual(r["summary"]["captured_captures"],0)
   self.assertFalse(r["summary"]["collection_complete"])
 def test_real_synthetic_fixture_is_validated(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session=self.create_plan(root)
   other=root/"other";other.mkdir()
   source=capture(other,"EXP-01-CP-01-R01","Corridor")
   target=session/"FP-EXP-01-CP-01-R01";shutil.rmtree(target);shutil.move(str(source),target)
   r=audit_session(session)
   self.assertEqual(r["summary"]["validated_captures"],1)
   self.assertEqual(r["summary"]["planned_captures"],1)
 def test_core_files_without_complete_dump_are_captured_not_validated(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.create_plan(Path(td));d=session/"FP-EXP-01-CP-01-R01"
   (d/"state.bin").write_bytes(b"partial");(d/"state.txt").write_text("partial")
   (d/"graphics"/"framebuffer.png").write_bytes(b"partial")
   r=audit_session(session)
   self.assertEqual(r["captures"][0]["status"],"captured")
   self.assertEqual(r["summary"]["validated_captures"],0)
 def test_path_traversal_is_invalid(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.create_plan(Path(td));d=session/"FP-EXP-01-CP-01-R01"
   p=d/"capture_metadata.json";m=json.loads(p.read_text());m["capture"]["state_file"]="../../outside";p.write_text(json.dumps(m))
   r=audit_session(session)
   self.assertEqual(r["captures"][0]["status"],"invalid")
 def test_session_plan_identity_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.create_plan(Path(td));p=session/"session_plan.json";m=json.loads(p.read_text());m["session_id"]="SESSION-OTHER";p.write_text(json.dumps(m))
   with self.assertRaises(CollectionError):audit_session(session)

if __name__=="__main__":unittest.main()
