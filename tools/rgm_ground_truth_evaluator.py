#!/usr/bin/env python3
"""Calibrate room-match threshold on calibration pairs and evaluate once on holdout pairs.

Requires explicit human-verified room annotations. Observed capture labels are
never silently promoted to ground truth.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
from typing import Any

class EvaluationError(Exception): pass

def load_json(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:raise EvaluationError(f"cannot read {path}: {e}") from e

def verified_annotations(path:Path)->dict[str,str]:
    raw=load_json(path)
    if raw.get("schema_version")!=1 or not isinstance(raw.get("annotations"),list):
        raise EvaluationError("annotation file must use schema_version 1 and an annotations array")
    out={}
    for i,item in enumerate(raw["annotations"]):
        if not isinstance(item,dict):raise EvaluationError(f"annotation {i} must be an object")
        cid=item.get("capture_id");room=item.get("room_id")
        if not isinstance(cid,str) or not cid or not isinstance(room,str) or not room:
            raise EvaluationError(f"annotation {i} needs capture_id and room_id")
        if item.get("verified") is not True:continue
        for field in ("reviewer","evidence"):
            if not isinstance(item.get(field),str) or not item[field].strip():
                raise EvaluationError(f"verified annotation {cid} requires non-empty {field}")
        if cid in out:raise EvaluationError(f"duplicate annotation for capture_id {cid}")
        out[cid]=room.strip().casefold()
    return out

def _pair_score(pair:dict[str,Any])->float|None:
    env=pair.get("environment",{})
    value=env.get("mean_available_map_similarity")
    if value is None:
        maps=env.get("map_comparisons",{})
        vals=[v.get("best_alignment",{}).get("weighted_similarity") for v in maps.values() if v.get("best_alignment")]
        vals=[x for x in vals if isinstance(x,(int,float)) and math.isfinite(x)]
        value=sum(vals)/len(vals) if vals else None
    if not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:return None
    return float(value)

def _metrics(pairs,threshold):
    tp=fp=tn=fn=0
    for p in pairs:
        pred=p["similarity"]>=threshold;truth=p["same_room"]
        if pred and truth:tp+=1
        elif pred and not truth:fp+=1
        elif not pred and not truth:tn+=1
        else:fn+=1
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    specificity=tn/(tn+fp) if tn+fp else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    accuracy=(tp+tn)/len(pairs) if pairs else 0.0
    balanced=(recall+specificity)/2 if (tp+fn and tn+fp) else None
    return {"pairs":len(pairs),"true_positive":tp,"false_positive":fp,"true_negative":tn,"false_negative":fn,
      "accuracy":accuracy,"precision":precision,"recall":recall,"specificity":specificity,"f1":f1,"balanced_accuracy":balanced}

def evaluate_dataset(split_path:Path,annotation_path:Path,correlation_path:Path)->dict[str,Any]:
    split=load_json(split_path);corr=load_json(correlation_path);annotations=verified_annotations(annotation_path)
    if split.get("schema_version")!=1 or not isinstance(split.get("assignments"),dict):
        raise EvaluationError("split manifest must use schema_version 1 and assignments object")
    if not isinstance(corr.get("pair_correlations"),list):raise EvaluationError("correlation report has no pair_correlations array")
    assignments=split["assignments"]
    for cid,sp in assignments.items():
        if sp not in ("train","calibration","evaluation","quarantine"):raise EvaluationError(f"invalid split for {cid}: {sp}")
    pairs=[];skipped={"unverified_annotation":0,"missing_split":0,"cross_split":0,"unsupported_split":0,"missing_similarity":0}
    seen=set()
    for raw in corr["pair_correlations"]:
        a,b=raw.get("capture_a"),raw.get("capture_b")
        if not isinstance(a,str) or not isinstance(b,str) or a==b:continue
        key=tuple(sorted((a,b)))
        if key in seen:continue
        seen.add(key)
        if a not in annotations or b not in annotations:skipped["unverified_annotation"]+=1;continue
        if a not in assignments or b not in assignments:skipped["missing_split"]+=1;continue
        sa,sb=assignments[a],assignments[b]
        if sa!=sb:skipped["cross_split"]+=1;continue
        if sa not in ("calibration","evaluation"):skipped["unsupported_split"]+=1;continue
        score=_pair_score(raw)
        if score is None:skipped["missing_similarity"]+=1;continue
        pairs.append({"capture_a":a,"capture_b":b,"split":sa,"similarity":score,
          "same_room":annotations[a]==annotations[b]})
    calibration=[p for p in pairs if p["split"]=="calibration"]
    evaluation=[p for p in pairs if p["split"]=="evaluation"]
    threshold=None;cal_metrics=None;eval_metrics=None;status="insufficient_evidence"
    if calibration:
        labels={p["same_room"] for p in calibration}
        if labels=={True,False}:
            vals=sorted({p["similarity"] for p in calibration})
            candidates=sorted({0.0,1.0,*vals,*[(a+b)/2 for a,b in zip(vals,vals[1:])]})
            ranked=[]
            for t in candidates:
                m=_metrics(calibration,t)
                if m["balanced_accuracy"] is not None:
                    ranked.append((m["balanced_accuracy"],m["f1"],-t,t,m))
            if ranked:
                _,_,_,threshold,cal_metrics=max(ranked,key=lambda x:(x[0],x[1],x[2]))
                if evaluation:
                    eval_metrics=_metrics(evaluation,threshold);status="evaluated"
                else:status="calibrated_no_holdout_pairs"
        else:status="calibration_needs_both_classes"
    return {"schema_version":1,"tool":"RGM Ground-Truth Threshold Evaluator","status":status,
      "threshold":threshold,"calibration_metrics":cal_metrics,"evaluation_metrics":eval_metrics,
      "pair_counts":{"eligible_total":len(pairs),"calibration":len(calibration),"evaluation":len(evaluation)},
      "skipped_pairs":skipped,"annotation_count_verified":len(annotations),
      "policy":{"threshold_selection":"Maximize balanced accuracy on calibration pairs; tie-break by F1, then prefer the higher threshold.",
       "holdout":"Evaluation pairs are never used to select the threshold.",
       "labels":"Only annotations with verified=true, reviewer and evidence are accepted.",
       "scope":"Pairwise rendered-map similarity only; not proof of generalization to unseen rooms, games or scene classes.",
       "minimum":"Calibration requires both same-room and different-room pairs. Metrics are descriptive; confidence intervals and larger independent datasets are still required."}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("split_manifest",type=Path);p.add_argument("annotations",type=Path);p.add_argument("correlations",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    try:
        result=evaluate_dataset(a.split_manifest,a.annotations,a.correlations);payload=json.dumps(result,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\n",encoding="utf-8");print(f"Evaluation written: {a.output}")
        else:print(payload)
        return 0 if result["status"]=="evaluated" else 1
    except (OSError,ValueError,KeyError,EvaluationError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
