import json,tempfile,unittest
from pathlib import Path
from tools.rgm_ground_truth_evaluator import evaluate_dataset,EvaluationError

def pair(a,b,score):
    return {"capture_a":a,"capture_b":b,"environment":{"mean_available_map_similarity":score}}

class GroundTruthEvaluatorTests(unittest.TestCase):
    def files(self,root,annotations,pairs):
        split={"schema_version":1,"assignments":{
          "A":"calibration","B":"calibration","C":"calibration",
          "D":"evaluation","E":"evaluation","F":"evaluation",
          "X":"train"}}
        (root/"split.json").write_text(json.dumps(split))
        (root/"annotations.json").write_text(json.dumps({"schema_version":1,"annotations":annotations}))
        (root/"correlations.json").write_text(json.dumps({"pair_correlations":pairs}))
        return root/"split.json",root/"annotations.json",root/"correlations.json"

    def annotations(self,ids):
        rooms={"A":"room-1","B":"room-1","C":"room-2","D":"room-1","E":"room-1","F":"room-2","X":"room-1"}
        return [{"capture_id":i,"room_id":rooms[i],"verified":True,"reviewer":"reviewer-1","evidence":"manual room comparison"} for i in ids]

    def test_calibrates_only_on_calibration_and_evaluates_holdout(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pairs=[pair("A","B",.9),pair("A","C",.2),pair("B","C",.3),
              pair("D","E",.8),pair("D","F",.1),pair("E","F",.4),pair("A","D",.99)]
            f=self.files(root,self.annotations(list("ABCDEF")),pairs)
            r=evaluate_dataset(*f)
            self.assertEqual(r["status"],"evaluated")
            self.assertAlmostEqual(r["threshold"],.6)
            self.assertEqual(r["calibration_metrics"]["balanced_accuracy"],1.0)
            self.assertEqual(r["evaluation_metrics"]["balanced_accuracy"],1.0)
            self.assertEqual(r["skipped_pairs"]["cross_split"],1)

    def test_unverified_labels_are_not_used(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);anns=self.annotations(list("ABC"))
            for a in anns:a["verified"]=False
            f=self.files(root,anns,[pair("A","B",.9),pair("A","C",.2),pair("B","C",.3)])
            r=evaluate_dataset(*f)
            self.assertEqual(r["status"],"insufficient_evidence")
            self.assertEqual(r["pair_counts"]["eligible_total"],0)
            self.assertEqual(r["skipped_pairs"]["unverified_annotation"],3)

    def test_requires_both_calibration_classes(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);anns=self.annotations(list("ABC"))
            f=self.files(root,anns,[pair("A","B",.9),pair("A","C",.8),pair("B","C",.7)])
            r=evaluate_dataset(*f)
            self.assertEqual(r["status"],"calibration_needs_both_classes")
            self.assertIsNone(r["threshold"])

    def test_verified_annotation_requires_reviewer_and_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);anns=self.annotations(list("ABC"));anns[0]["evidence"]=""
            f=self.files(root,anns,[pair("A","B",.9)])
            with self.assertRaises(EvaluationError):evaluate_dataset(*f)

if __name__=="__main__":unittest.main()
