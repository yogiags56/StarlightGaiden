import json,tempfile,unittest
from pathlib import Path
from tools.rgm_experiment_plan import load_matrix,generate
class ExperimentPlanTests(unittest.TestCase):
 def matrix(self):
  return {"schema_version":1,"milestone":"RGM-001E.9","project":"Test","upstream":{"repository":"x","commit":"abc"},
   "protocol":{"repeat_count":3},"experiments":[{"id":"EXP-01","name":"Test","target":"exploration","sequence":["before","after"],"captures":["before","after"],"question":"Q?"}]}
 def test_generate_templates_without_game_data(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);m=root/"matrix.json";m.write_text(json.dumps(self.matrix()))
   result=generate(m,root/"SESSION-TEST","SESSION-TEST")
   self.assertEqual(result["planned_capture_checkpoints"],2);self.assertFalse(result["game_data_created"])
   f=root/"SESSION-TEST"/"EXP-01"/"EXP-01-CP-01.json";d=json.loads(f.read_text())
   self.assertEqual(d["verification"]["room_identity"],"unverified")
   self.assertFalse((f.parent/"state.bin").exists())
 def test_duplicate_experiment_ids_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"m.json";m=self.matrix();m["experiments"].append(m["experiments"][0]);p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):load_matrix(p)
 def test_invalid_session_id_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"m.json";p.write_text(json.dumps(self.matrix()))
   with self.assertRaises(ValueError):generate(p,Path(td)/"out","../escape")
if __name__=="__main__":unittest.main()
