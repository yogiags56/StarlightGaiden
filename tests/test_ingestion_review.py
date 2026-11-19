import json,shutil,tempfile,unittest
from pathlib import Path
from tools.rgm_ingestion_review import review_session,IngestionReviewError
from tools.rgm_experiment_plan import generate
from test_capture_validator import capture

def matrix():
 return {"schema_version":1,"milestone":"RGM-001E.9","project":"Test","upstream":{"repository":"x","commit":"abc"},
 "protocol":{"repeat_count":1},"experiments":[{"id":"EXP-01","name":"Test","target":"exploration","sequence":["before"],"captures":["before","after"],"question":"Q?"}]}

class IngestionReviewTests(unittest.TestCase):
 def setup_session(self,root):
  m=root/"matrix.json";m.write_text(json.dumps(matrix()))
  session=root/"SESSION-0001";generate(m,session,"SESSION-0001");return session
 def add_capture(self,root,session,cid,checkpoint):
  tmp=root/"tmp";tmp.mkdir(exist_ok=True)
  src=capture(tmp,cid,"Corridor")
  dst=session/("FP-"+cid);shutil.rmtree(dst,ignore_errors=True);shutil.move(str(src),dst)
  p=dst/"capture_metadata.json";meta=json.loads(p.read_text())
  meta.update({"session_id":"SESSION-0001","capture_id":cid,"experiment_id":"EXP-01","checkpoint":checkpoint,"repeat":1})
  p.write_text(json.dumps(meta))
  return dst
 def test_blank_session_is_planned(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.setup_session(Path(td));r=review_session(session)
   self.assertEqual(r["summary"]["planned_captures"],2)
   self.assertFalse(r["summary"]["complete"])
 def test_exact_plan_identity_and_checksum_coverage_validates(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session=self.setup_session(root)
   self.add_capture(root,session,"EXP-01-CP-01-R01","before")
   r=review_session(session)
   self.assertEqual(r["summary"]["validated_captures"],1)
   self.assertEqual(r["captures"][0]["checksum_coverage"],1.0)
 def test_wrong_checkpoint_is_invalid(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session=self.setup_session(root)
   self.add_capture(root,session,"EXP-01-CP-01-R01","wrong")
   r=review_session(session)
   self.assertEqual(r["captures"][0]["status"],"invalid")
   self.assertTrue(any("checkpoint mismatch" in e for e in r["captures"][0]["errors"]))
 def test_missing_checksum_keeps_capture_unvalidated(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session=self.setup_session(root);d=self.add_capture(root,session,"EXP-01-CP-01-R01","before")
   p=d/"capture_metadata.json";m=json.loads(p.read_text());m["source_sha256"].pop("state.txt");p.write_text(json.dumps(m))
   r=review_session(session)
   self.assertEqual(r["captures"][0]["status"],"captured")
   self.assertTrue(any("missing SHA-256 coverage" in w for w in r["captures"][0]["warnings"]))
 def test_unexpected_folder_is_reported(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session=self.setup_session(root)
   d=session/"FP-UNPLANNED";d.mkdir()
   (d/"capture_metadata.json").write_text("{}")
   r=review_session(session)
   self.assertEqual(r["summary"]["unexpected_capture_folders"],1)
   self.assertFalse(r["summary"]["complete"])
 def test_session_plan_identity_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   session=self.setup_session(Path(td));p=session/"session_plan.json";m=json.loads(p.read_text());m["session_id"]="OTHER";p.write_text(json.dumps(m))
   with self.assertRaises(IngestionReviewError):review_session(session)

if __name__=="__main__":unittest.main()
