import json,tempfile,unittest
from pathlib import Path
from tools.rgm_temporal_consistency import review_session,TemporalError

def session(root,timing_by_repeat=None):
 plan={"schema_version":1,"session_id":"SESSION-TEMP","experiments":[{"experiment_id":"EXP-01","capture_checkpoints":[
  {"capture_id":"EXP-01-CP-01-R01","checkpoint":"stationary","repeat":1},
  {"capture_id":"EXP-01-CP-01-R02","checkpoint":"stationary","repeat":2}]}]}
 (root/"session_plan.json").write_text(json.dumps(plan))
 for i in (1,2):
  cid=f"EXP-01-CP-01-R{i:02d}";d=root/("FP-"+cid);d.mkdir()
  m={"capture_id":cid,"capture_timing":(timing_by_repeat or {}).get(i)}
  (d/"capture_metadata.json").write_text(json.dumps(m))

def timing(ss=1_000_000_000,se=1_020_000_000,gs=1_030_000_000,ge=1_050_000_000,fs=100,fg=100,clock="monotonic:session"):
 return {"clock_id":clock,"clock_source":"time.monotonic_ns","state_dump_started_ns":ss,"state_dump_completed_ns":se,
 "graphics_dump_started_ns":gs,"graphics_dump_completed_ns":ge,"game_frame_at_state":fs,"game_frame_at_graphics":fg}

class TemporalConsistencyTests(unittest.TestCase):
 def test_matching_frame_and_short_gap_pass(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root,{1:timing(),2:timing(ss=2_000_000_000,se=2_020_000_000,gs=2_030_000_000,ge=2_050_000_000,fs=200,fg=200)})
   r=review_session(root,250)
   self.assertEqual(r["captures"][0]["status"],"time_window_pass")
   self.assertTrue(r["summary"]["all_captures_time_verified"])
 def test_frame_mismatch_invalid(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);t=timing(fg=101);session(root,{1:t,2:timing()})
   r=review_session(root)
   self.assertEqual(r["captures"][0]["status"],"invalid")
 def test_large_gap_requires_review(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root,{1:timing(gs=2_000_000_000,ge=2_020_000_000),2:timing()})
   r=review_session(root,100)
   self.assertEqual(r["captures"][0]["status"],"review_required")
 def test_missing_timing_insufficient(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root)
   r=review_session(root)
   self.assertEqual(r["captures"][0]["status"],"insufficient_evidence")
   self.assertIsNone(r["captures"][0]["frame_markers_match"])
 def test_missing_metadata_is_reported_without_crashing_summary(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   plan={"schema_version":1,"session_id":"SESSION-TEMP","experiments":[{"experiment_id":"EXP-01","capture_checkpoints":[{"capture_id":"EXP-01-CP-01-R01","checkpoint":"x","repeat":1}]}]}
   (root/"session_plan.json").write_text(json.dumps(plan))
   r=review_session(root)
   self.assertEqual(r["captures"][0]["status"],"insufficient_evidence")
   self.assertEqual(r["summary"]["frame_verified_captures"],0)
 def test_bad_interval_invalid(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root,{1:timing(ss=20,se=10),2:timing()})
   r=review_session(root)
   self.assertEqual(r["captures"][0]["status"],"invalid")
 def test_clock_source_id_is_reported(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root,{1:timing(clock="clock-A"),2:timing()})
   r=review_session(root)
   self.assertEqual(r["captures"][0]["clock_id"],"clock-A")
 def test_negative_gap_limit_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);session(root)
   with self.assertRaises(TemporalError):review_session(root,-1)

if __name__=="__main__":unittest.main()
