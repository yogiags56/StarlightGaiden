#!/usr/bin/env python3
"""Audit capture provenance and create leakage-resistant session-group splits.

Observed location labels are grouping hints, not verified room ground truth.
No room identity is inferred by this tool.
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any
try:
    from .rgm_capture_validator import inspect_capture, sha256_file
except ImportError:
    from rgm_capture_validator import inspect_capture, sha256_file

ARTIFACTS=("state_file","state_summary","graphics_directory")
GRAPHICS=("map_9800.png","map_9c00.png","framebuffer.png","manifest.txt")
SPLITS=("train","calibration","evaluation")

class DatasetAuditError(Exception): pass

def digest_capture(directory:Path, meta:dict[str,Any])->dict[str,str]:
    cap=meta["capture"]; result={}
    for key in ("state_file","state_summary"):
        p=directory/cap[key]
        if p.is_file(): result[key]=sha256_file(p)
    gd=directory/cap["graphics_directory"]
    for name in GRAPHICS:
        p=gd/name
        if p.is_file(): result[name]=sha256_file(p)
    return result

class UnionFind:
    def __init__(self,items): self.parent={x:x for x in items}
    def find(self,x):
        while self.parent[x]!=x:
            self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def union(self,a,b):
        ra,rb=self.find(a),self.find(b)
        if ra!=rb:self.parent[rb]=ra

def _stable_order(items,seed):
    return sorted(items,key=lambda x:hashlib.sha256((str(seed)+"|"+x).encode()).hexdigest())

def audit_dataset(dataset:Path,seed:int=20261119,ratios:dict[str,float]|None=None)->dict[str,Any]:
    if not dataset.is_dir(): raise DatasetAuditError(f"dataset directory not found: {dataset}")
    ratios=ratios or {"train":0.60,"calibration":0.20,"evaluation":0.20}
    if set(ratios)!=set(SPLITS) or any(v<=0 for v in ratios.values()) or abs(sum(ratios.values())-1)>1e-8:
        raise DatasetAuditError("split ratios must be positive train/calibration/evaluation values summing to 1")
    paths=sorted(dataset.glob("SESSION-*/FP-*/capture_metadata.json"))
    captures=[]; invalid=[]
    for mp in paths:
        d=mp.parent; report=inspect_capture(d)
        if report["status"]!="valid":
            invalid.append({"capture_id":report.get("capture_id"),"directory":str(d),"errors":report["errors"]});continue
        try: meta=json.loads(mp.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as e:
            invalid.append({"directory":str(d),"errors":[str(e)]});continue
        observed=meta.get("observed",{})
        label=observed.get("location_label","")
        label=label.strip() if isinstance(label,str) else ""
        hashes=digest_capture(d,meta)
        signature=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
        captures.append({"capture_id":meta["capture_id"],"session_id":meta["session_id"],"directory":str(d),
          "location_label":label or "unknown","activity":observed.get("activity","unknown"),
          "repeat":meta.get("repeat"),"artifact_sha256":hashes,"evidence_signature":signature})
    # Exact content duplicates are identified across captures; session and duplicate links are
    # unioned so no recording session or exact evidence duplicate crosses a split boundary.
    ids=[c["capture_id"] for c in captures]
    if len(ids)!=len(set(ids)): raise DatasetAuditError("duplicate capture_id values found across dataset")
    uf=UnionFind(ids); session_first={}; signature_first={}
    for c in captures:
        sid=c["session_id"];sig=c["evidence_signature"];cid=c["capture_id"]
        if sid in session_first:uf.union(cid,session_first[sid])
        else:session_first[sid]=cid
        if sig in signature_first:uf.union(cid,signature_first[sig])
        else:signature_first[sig]=cid
    components={}
    for c in captures:components.setdefault(uf.find(c["capture_id"]),[]).append(c)
    eligible=[];quarantine=[]
    for root,group in components.items():
        labels=sorted({c["location_label"].casefold() for c in group if c["location_label"].casefold() not in ("","unknown","unlabelled","unlabeled")})
        if not labels:
            quarantine.extend(c["capture_id"] for c in group);continue
        eligible.append({"group_id":hashlib.sha256("|".join(sorted(c["capture_id"] for c in group)).encode()).hexdigest()[:16],
          "capture_ids":sorted(c["capture_id"] for c in group),"session_ids":sorted({c["session_id"] for c in group}),
          "labels":labels,"size":len(group)})
    assignments={};split_groups={s:[] for s in SPLITS};counts={s:0 for s in SPLITS}
    ordered=sorted(eligible,key=lambda g:(-g["size"],hashlib.sha256((str(seed)+"|"+g["group_id"]).encode()).hexdigest()))
    if len(ordered)>=3:
        for i,g in enumerate(ordered):
            if i<3: chosen=SPLITS[i]
            else:
                chosen=min(SPLITS,key=lambda s:(counts[s]/max(ratios[s],1e-9),SPLITS.index(s)))
            split_groups[chosen].append(g["group_id"]);counts[chosen]+=g["size"]
            for cid in g["capture_ids"]:assignments[cid]=chosen
    else:
        quarantine.extend(cid for g in ordered for cid in g["capture_ids"])
    capture_index={c["capture_id"]:c for c in captures}
    duplicates=[]
    for sig,group in _group_by_signature(captures).items():
        if len(group)>1:duplicates.append({"evidence_signature":sig,"capture_ids":sorted(c["capture_id"] for c in group)})
    label_sessions={}
    for c in captures:
        if c["location_label"].casefold() not in ("","unknown","unlabelled","unlabeled"):
            label_sessions.setdefault(c["location_label"],set()).add(c["session_id"])
    return {"schema_version":1,"tool":"RGM Dataset Audit","dataset":str(dataset),"seed":seed,
      "split_ratios":ratios,"summary":{"capture_directories_found":len(paths),"captures_valid":len(captures),
       "captures_invalid":len(invalid),"exact_duplicate_groups":len(duplicates),"eligible_session_duplicate_groups":len(eligible),
       "independent_groups":len(eligible),"labelled_captures":sum(c["location_label"].casefold() not in ("","unknown","unlabelled","unlabeled") for c in captures),
       "quarantined_captures":len(set(quarantine)),"split_counts":counts,
       "evaluation_ready":len(eligible)>=3 and all(counts[s]>0 for s in SPLITS)},
      "invalid_captures":invalid,"exact_duplicates":duplicates,"captures":[{**c,"split":assignments.get(c["capture_id"],"quarantine")} for c in captures],
      "groups":[{**g,"split":next((s for s in SPLITS if g["group_id"] in split_groups[s]),"quarantine")} for g in eligible],
      "quarantine_capture_ids":sorted(set(quarantine)),
      "label_session_counts":{k:len(v) for k,v in sorted(label_sessions.items())},
      "split_groups":split_groups,
      "policy":{"grouping":"All captures from one session and all exact evidence duplicates are kept in one connected split group.",
       "unknown_labels":"Quarantined; excluded from supervised split assignment.",
       "labels":"Observed operator labels are unverified and are not ground truth.",
       "evaluation":"A split manifest is only structurally ready when at least three independent groups exist. It does not establish sufficient class coverage or ground-truth validity.",
       "duplicates":"Exact duplicate evidence is detected using SHA-256 over available state summary/binary and selected graphics artifacts."}}

def _group_by_signature(captures):
    out={}
    for c in captures:out.setdefault(c["evidence_signature"],[]).append(c)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("dataset",type=Path)
    p.add_argument("--seed",type=int,default=20261119);p.add_argument("--output",type=Path)
    p.add_argument("--split-manifest",type=Path,help="Optional path for capture_id-to-split JSON")
    a=p.parse_args()
    try:
        report=audit_dataset(a.dataset,a.seed);payload=json.dumps(report,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\n",encoding="utf-8");print(f"Audit written: {a.output}")
        else:print(payload)
        if a.split_manifest:
            manifest={"schema_version":1,"seed":report["seed"],"evaluation_ready":report["summary"]["evaluation_ready"],
              "assignments":{c["capture_id"]:c["split"] for c in report["captures"]}}
            a.split_manifest.write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
            print(f"Split manifest written: {a.split_manifest}")
        return 0
    except (OSError,ValueError,KeyError,DatasetAuditError) as e:
        print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
