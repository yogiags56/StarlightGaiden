#!/usr/bin/env python3
"""Report planned/captured/validated progress for an RGM capture session."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
try:
    from .rgm_capture_validator import inspect_capture
except ImportError:
    from rgm_capture_validator import inspect_capture

class CollectionError(Exception):pass

def _safe_child(root:Path,value:str)->Path:
    if not isinstance(value,str) or not value:raise CollectionError("capture path must be a non-empty relative path")
    base=root.resolve();p=(root/value).resolve()
    if p!=base and base not in p.parents:raise CollectionError("capture path escapes its folder")
    return p

def audit_session(session_dir:Path)->dict:
    plan_path=session_dir/"session_plan.json"
    if not plan_path.is_file():raise CollectionError(f"session_plan.json missing: {session_dir}")
    try:plan=json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:raise CollectionError(f"invalid session plan: {e}") from e
    if plan.get("schema_version")!=1 or not isinstance(plan.get("session_id"),str):
        raise CollectionError("unsupported session plan schema or missing session_id")
    if session_dir.name.startswith("SESSION-") and plan["session_id"]!=session_dir.name:
        raise CollectionError("session_id does not match session directory")
    experiments=plan.get("experiments")
    if not isinstance(experiments,list) or not experiments:raise CollectionError("session plan has no experiments")
    rows=[];seen=set()
    for exp in experiments:
        if not isinstance(exp,dict) or not isinstance(exp.get("capture_checkpoints"),list):
            raise CollectionError("invalid experiment checkpoint list")
        for checkpoint in exp["capture_checkpoints"]:
            cid=checkpoint.get("capture_id")
            if not isinstance(cid,str) or not cid:raise CollectionError("checkpoint has no capture_id")
            if cid in seen:raise CollectionError(f"duplicate planned capture_id: {cid}")
            seen.add(cid);directory=session_dir/("FP-"+cid)
            meta_path=directory/"capture_metadata.json"
            if not meta_path.is_file():
                status="planned";errors=["capture metadata template missing"]
            else:
                try:meta=json.loads(meta_path.read_text(encoding="utf-8"))
                except (OSError,json.JSONDecodeError) as e:
                    status="invalid";errors=[f"metadata: {e}"]
                else:
                    if meta.get("capture_id")!=cid:status="invalid";errors=["capture_id mismatch"]
                    elif meta.get("session_id")!=plan["session_id"]:status="invalid";errors=["session_id mismatch"]
                    else:
                        report=inspect_capture(directory)
                        errors=report["errors"]
                        if report["status"]=="valid":status="validated"
                        else:
                            cap=meta.get("capture",{}) if isinstance(meta.get("capture"),dict) else {}
                            try:
                                state_path=_safe_child(directory,cap.get("state_file"))
                                summary_path=_safe_child(directory,cap.get("state_summary"))
                                graphics_path=_safe_child(directory,cap.get("graphics_directory"))
                                has_state=state_path.is_file()
                                has_summary=summary_path.is_file()
                                has_graphics=graphics_path.is_dir() and any((graphics_path/n).is_file() for n in ("framebuffer.png","map_9800.png","map_9c00.png"))
                                status="captured" if has_state and has_summary and has_graphics else "planned"
                            except CollectionError as e:
                                status="invalid";errors.append(str(e))
            rows.append({"capture_id":cid,"experiment_id":exp.get("experiment_id"),"checkpoint":checkpoint.get("checkpoint"),
              "repeat":checkpoint.get("repeat"),"status":status,"errors":errors})
    counts={s:sum(r["status"]==s for r in rows) for s in ("planned","captured","validated","invalid")}
    total=len(rows)
    return {"schema_version":1,"tool":"RGM Collection Status","session_id":plan["session_id"],
      "summary":{"experiments":len(experiments),"planned_checkpoints":total,**{f"{k}_captures":v for k,v in counts.items()},
        "validated_percent":round(100*counts["validated"]/total,2) if total else 0,
        "collection_complete":total>0 and counts["validated"]==total},
      "captures":rows,
      "policy":{"planned":"No complete paired state and graphics data detected.",
        "captured":"Core files exist but the strict capture validator has not accepted the capture.",
        "validated":"The existing capture validator accepted snapshot, summary, graphics dimensions/manifest and integrity checks.",
        "verified":"Human ground-truth room annotation is tracked separately; validation does not mean room identity is verified.",
        "scope":"This report reads files and does not modify or fabricate capture data."}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("session",type=Path);p.add_argument("--output",type=Path);a=p.parse_args()
    try:
        report=audit_session(a.session);payload=json.dumps(report,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\\n",encoding="utf-8");print(f"Collection report written: {a.output}")
        else:print(payload)
        return 0 if report["summary"]["invalid_captures"]==0 else 1
    except (OSError,ValueError,CollectionError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
