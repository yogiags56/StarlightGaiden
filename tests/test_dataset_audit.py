import hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from tools.rgm_dataset_audit import audit_dataset
from test_capture_validator import capture

def make_capture(root,session,cid,label,variation):
    original=capture(root,cid,label)
    target_parent=root/session;target_parent.mkdir(parents=True,exist_ok=True)
    target=target_parent/original.name
    shutil.move(str(original),target)
    meta_path=target/"capture_metadata.json"
    meta=json.loads(meta_path.read_text())
    meta["session_id"]=session
    (target/"state.txt").write_text(f"ROM_BANK=1\nvariation={variation}\n")
    checks={}
    for rel in ("state.bin","state.txt","graphics/map_9800.png","graphics/map_9c00.png","graphics/framebuffer.png","graphics/manifest.txt"):
        p=target/rel;checks[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    meta["source_sha256"]=checks
    meta_path.write_text(json.dumps(meta))
    return target

class DatasetAuditTests(unittest.TestCase):
    def test_grouped_split_no_session_leakage_and_unknown_quarantine(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for n,label in ((1,"Corridor A"),(2,"Corridor B"),(3,"Engine Room")):
                make_capture(root,f"SESSION-{n}",f"EXP-{n}-A",label,f"{n}-a")
                make_capture(root,f"SESSION-{n}",f"EXP-{n}-B",label,f"{n}-b")
            make_capture(root,"SESSION-UNKNOWN","EXP-UNKNOWN","unknown","unknown")
            report=audit_dataset(root,seed=17)
            self.assertEqual(report["summary"]["captures_valid"],7)
            self.assertEqual(report["summary"]["independent_groups"],3)
            self.assertEqual(report["summary"]["quarantined_captures"],1)
            self.assertTrue(report["summary"]["evaluation_ready"])
            by_session={}
            for item in report["captures"]:
                if item["session_id"]!="SESSION-UNKNOWN":
                    by_session.setdefault(item["session_id"],set()).add(item["split"])
                else:self.assertEqual(item["split"],"quarantine")
            self.assertTrue(all(len(splits)==1 for splits in by_session.values()))
            self.assertEqual({len(report["split_groups"][s]) for s in ("train","calibration","evaluation")},{1})

    def test_deterministic_manifest_and_duplicate_grouping(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=make_capture(root,"SESSION-1","EXP-1-A","Corridor A","same")
            make_capture(root,"SESSION-2","EXP-2-A","Corridor B","different")
            make_capture(root,"SESSION-3","EXP-3-A","Engine Room","third")
            # A copied capture in another session is an exact evidence duplicate and must stay grouped.
            dup_parent=root/"SESSION-4";dup_parent.mkdir()
            dup=dup_parent/"FP-EXP-4-A";shutil.copytree(a,dup)
            meta_path=dup/"capture_metadata.json";meta=json.loads(meta_path.read_text());meta["session_id"]="SESSION-4";meta["capture_id"]="EXP-4-A";meta_path.write_text(json.dumps(meta))
            first=audit_dataset(root,seed=99);second=audit_dataset(root,seed=99)
            self.assertEqual(first["captures"],second["captures"])
            self.assertEqual(first["summary"]["exact_duplicate_groups"],1)
            assignments={x["capture_id"]:x["split"] for x in first["captures"]}
            self.assertEqual(assignments["EXP-1-A"],assignments["EXP-4-A"])
            self.assertEqual(first["summary"]["independent_groups"],3)
            self.assertTrue(first["summary"]["evaluation_ready"])

    def test_invalid_split_ratios_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):audit_dataset(Path(td),ratios={"train":0.5,"calibration":0.5,"evaluation":0.5})

if __name__=="__main__":unittest.main()
