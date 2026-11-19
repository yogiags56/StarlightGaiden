#!/usr/bin/env python3
"""Strictly review one planned RGM session against its capture plan and file provenance."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
from typing import Any
try:
    from .rgm_capture_validator import inspect_capture,sha256_file
except ImportError:
    from rgm_capture_validator import inspect_capture,sha256_file

class IngestionReviewError(Exception):pass

def _read_json(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:raise IngestionReviewError(f"{path}: {e}") from e

def _safe(root:Path,rel:Any)->Path:
    if not isinstance(rel,str) or not rel:raise IngestionReviewError("artifact path must be non-empty")
    base=root.resolve();p=(root/rel).resolve()
    if p!=base and base not in p.parents:raise IngestionReviewError(f"path escapes capture folder: {rel}")
    return p

def _expected(plan:dict)->dict[str,dict]:
    expected={}
    for exp in plan["experiments"]:
        for cp in exp["capture_checkpoints"]:
            cid=cp["capture_id"]
            if cid in expected:raise IngestionReviewError(f"duplicate planned capture_id: {cid}")
            expected[cid]={"experiment_id":exp["experiment_id"],"checkpoint":cp["checkpoint"],"repeat":cp["repeat"]}
    return expected

def review_session(session:Path)->dict[str,Any]:
    plan=_read_json(session/"session_plan.json")
    if plan.get("schema_version")!=1 or not isinstance(plan.get("session_id"),str) or not isinstance(plan.get("experiments"),list):
        raise IngestionReviewError("invalid session_plan schema")
    if session.name.startswith("SESSION-") and plan["session_id"]!=session.name:
        raise IngestionReviewError("session directory and plan session_id mismatch")
    expected=_expected(plan);rows=[];seen=set();unexpected=[]
    folders={p.name[3:]:p for p in session.glob("FP-*/capture_metadata.json") if p.parent.is_dir()}
    for cid,identity in expected.items():
        folder=session/("FP-"+cid);mp=folder/"capture_metadata.json"
        if not mp.is_file():
            rows.append({"capture_id":cid,**identity,"status":"planned","errors":["capture metadata missing"],"warnings":[]})
            continue
        m=_read_json(mp);errors=[];warnings=[]
        if cid in seen:errors.append("duplicate capture folder")
        seen.add(cid)
        for key,value in (("capture_id",cid),("session_id",plan["session_id"]),("experiment_id",identity["experiment_id"]),("checkpoint",identity["checkpoint"]),("repeat",identity["repeat"])):
            if m.get(key)!=value:errors.append(f"{key} mismatch: expected {value!r}, got {m.get(key)!r}")
        base_report=inspect_capture(folder)
        errors.extend(base_report["errors"])
        warnings.extend(base_report["warnings"])
        cap=m.get("capture") if isinstance(m.get("capture"),dict) else {}
        artifact_paths=[]
        try:
            for key in ("state_file","state_summary"):
                p=_safe(folder,cap.get(key));artifact_paths.append((key,p))
            gd=_safe(folder,cap.get("graphics_directory"))
            if gd.is_dir():
                for p in sorted(gd.rglob("*")):
                    if p.is_file():
                        rel=p.relative_to(folder).as_posix()
                        artifact_paths.append((rel,p))
        except IngestionReviewError as e:errors.append(str(e));gd=None
        checks=m.get("source_sha256")
        if not isinstance(checks,dict):checks={}
        required={p.relative_to(folder).as_posix():p for _,p in artifact_paths if p.is_file()}
        missing=sorted(set(required)-set(checks))
        extra=sorted(set(checks)-set(required))
        mismatched=[]
        for rel,p in required.items():
            if rel in checks:
                try:
                    if not isinstance(checks[rel],str) or sha256_file(p).lower()!=checks[rel].lower():mismatched.append(rel)
                except OSError as e:errors.append(f"cannot hash {rel}: {e}")
        if missing:warnings.append("missing SHA-256 coverage: "+", ".join(missing))
        if extra:warnings.append("checksum entries do not map to discovered required artifacts: "+", ".join(extra))
        if mismatched:errors.append("SHA-256 mismatch: "+", ".join(mismatched))
        observed=m.get("observed") if isinstance(m.get("observed"),dict) else {}
        for key in ("location_label","activity","character","speaker"):
            value=observed.get(key)
            if not isinstance(value,str) or not value.strip() or value.strip().casefold() in ("unknown","unrecorded","n/a"):
                warnings.append(f"observed.{key} needs operator review")
        if errors:status="invalid"
        elif base_report["status"]=="valid" and not missing and not extra and not mismatched:status="validated"
        elif required:status="captured"
        else:status="planned"
        rows.append({"capture_id":cid,**identity,"status":status,"errors":errors,"warnings":warnings,
          "artifact_count":len(required),"checksum_coverage":len(set(required)&set(checks))/len(required) if required else 0.0})
    for cid,folder in folders.items():
        if cid not in expected:unexpected.append({"capture_id":cid,"directory":str(folder),"status":"unexpected"})
    counts={s:sum(r["status"]==s for r in rows) for s in ("planned","captured","validated","invalid")}
    return {"schema_version":1,"tool":"RGM Strict Ingestion Review","session_id":plan["session_id"],
      "summary":{"planned_records":len(expected),**{s+"_captures":v for s,v in counts.items()},
        "unexpected_capture_folders":len(unexpected),"complete":bool(rows) and counts["validated"]==len(rows) and not unexpected,
        "operator_review_required":sum(bool(r["warnings"]) for r in rows)},
      "captures":rows,"unexpected_folders":unexpected,
      "policy":{"validated":"Plan identity, base capture validator, required artifact presence and exact SHA-256 coverage all pass.",
        "warnings":"Missing/unknown observed labels are review prompts, not automatic identity assertions.",
        "ground_truth":"This tool does not verify room, scene, character or speaker identity.",
        "scope":"Read-only audit; no files are created, repaired or rewritten."}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("session",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    try:
        result=review_session(a.session);payload=json.dumps(result,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\n",encoding="utf-8");print(f"Review written: {a.output}")
        else:print(payload)
        return 1 if result["summary"]["invalid_captures"] or result["summary"]["unexpected_capture_folders"] else 0
    except (OSError,ValueError,KeyError,IngestionReviewError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
