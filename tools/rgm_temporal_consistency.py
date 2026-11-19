#!/usr/bin/env python3
"""Audit temporal evidence linking state and graphics dumps within each capture."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any

class TemporalError(Exception):pass

def _load(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e:raise TemporalError(f"{path}: {e}") from e

def _nonnegative_int(obj:dict,key:str):
    v=obj.get(key)
    if isinstance(v,bool) or not isinstance(v,int) or v<0:
        raise ValueError(f"{key} must be a non-negative integer")
    return v

def _timing(meta:dict,max_gap_ms:float):
    t=meta.get("capture_timing")
    if not isinstance(t,dict):return {"status":"insufficient_evidence","errors":[],"warnings":["capture_timing block absent"]}
    errors=[];warnings=[]
    clock=t.get("clock_id")
    source=t.get("clock_source")
    if not isinstance(clock,str) or not clock.strip():errors.append("clock_id missing")
    if not isinstance(source,str) or not source.strip():warnings.append("clock_source not documented")
    try:
        ss=_nonnegative_int(t,"state_dump_started_ns");se=_nonnegative_int(t,"state_dump_completed_ns")
        gs=_nonnegative_int(t,"graphics_dump_started_ns");ge=_nonnegative_int(t,"graphics_dump_completed_ns")
        if se<ss:errors.append("state dump completion precedes start")
        if ge<gs:errors.append("graphics dump completion precedes start")
        state_mid=(ss+se)//2;graphics_mid=(gs+ge)//2
        gap=abs(graphics_mid-state_mid)/1_000_000
        if ss>ge or gs>se:
            # Sequential operations are expected; this is not itself a failure.
            warnings.append("state and graphics dump intervals do not overlap; midpoint gap is used")
        if gap>max_gap_ms:warnings.append(f"dump midpoint gap {gap:.3f} ms exceeds configured {max_gap_ms:.3f} ms")
    except ValueError as e:
        errors.append(str(e));gap=None
    frame_state=t.get("game_frame_at_state")
    frame_graphics=t.get("game_frame_at_graphics")
    frame_match=None
    if isinstance(frame_state,int) and not isinstance(frame_state,bool) and isinstance(frame_graphics,int) and not isinstance(frame_graphics,bool):
        frame_match=frame_state==frame_graphics
        if not frame_match:errors.append("game frame markers differ between state and graphics dumps")
    else:
        warnings.append("frame-counter evidence missing; timestamp proximity cannot prove identical game state")
    utc_state=t.get("state_dump_utc");utc_graphics=t.get("graphics_dump_utc")
    if bool(utc_state)!=bool(utc_graphics):warnings.append("only one UTC timestamp supplied")
    status="invalid" if errors else ("time_window_pass" if gap is not None and gap<=max_gap_ms and frame_match is True else "review_required")
    return {"status":status,"errors":errors,"warnings":warnings,"clock_id":clock,
      "midpoint_gap_ms":round(gap,3) if gap is not None else None,"frame_markers_match":frame_match,
      "state_frame":frame_state,"graphics_frame":frame_graphics}

def review_session(session:Path,max_gap_ms:float=250.0)->dict[str,Any]:
    if max_gap_ms<0:raise TemporalError("max_gap_ms must be non-negative")
    plan=_load(session/"session_plan.json")
    if plan.get("schema_version")!=1 or not isinstance(plan.get("experiments"),list):raise TemporalError("invalid session plan")
    rows=[];groups={}
    for exp in plan["experiments"]:
        for cp in exp["capture_checkpoints"]:
            cid=cp["capture_id"];folder=session/("FP-"+cid);mp=folder/"capture_metadata.json"
            if not mp.is_file():
                result={"status":"insufficient_evidence","errors":[],"warnings":["capture metadata missing"]}
                meta={}
            else:
                meta=_load(mp);result=_timing(meta,max_gap_ms)
            row={"capture_id":cid,"experiment_id":exp["experiment_id"],"checkpoint":cp["checkpoint"],
                 "repeat":cp["repeat"],**result}
            rows.append(row);groups.setdefault((exp["experiment_id"],str(cp["checkpoint"])),[]).append(row)
    repeat_reviews=[]
    for (eid,checkpoint),items in groups.items():
        if len(items)<2:continue
        known=[x for x in items if x["status"] in ("time_window_pass","review_required","invalid")]
        repeat_reviews.append({"experiment_id":eid,"checkpoint":checkpoint,"repeat_count":len(items),
          "timing_evidence_count":len(known),"all_repeats_have_timing_evidence":len(known)==len(items),
          "frame_marker_mismatch_count":sum("game frame markers differ between state and graphics dumps" in x["errors"] for x in items),
          "note":"Different repeats are separate gameplay moments; their frame numbers are not expected to match."})
    counts={s:sum(x["status"]==s for x in rows) for s in ("time_window_pass","review_required","insufficient_evidence","invalid")}
    return {"schema_version":1,"tool":"RGM Temporal Consistency Auditor","session_id":plan.get("session_id"),
      "configuration":{"max_dump_midpoint_gap_ms":max_gap_ms},
      "summary":{"planned_captures":len(rows),**{k+"_captures":v for k,v in counts.items()},
        "frame_verified_captures":sum(x["frame_markers_match"] is True for x in rows),
        "all_captures_time_verified":bool(rows) and counts["time_window_pass"]==len(rows)},
      "captures":rows,"repeat_reviews":repeat_reviews,
      "interpretation":{"time_window_pass":"Both dump intervals have valid monotonic timestamps within the configured midpoint gap and matching frame markers.",
        "review_required":"Timing is incomplete, too far apart, or lacks matching frame-counter proof.",
        "insufficient_evidence":"No usable timing block exists.",
        "invalid":"Malformed timing or contradictory frame markers.",
        "limitation":"A close timestamp alone does not prove the game state was unchanged. Matching frame markers are stronger evidence only if the runtime counter is trustworthy and sampled atomically with each dump."}}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("session",type=Path);p.add_argument("--max-gap-ms",type=float,default=250.0);p.add_argument("--output",type=Path);a=p.parse_args()
    try:
        result=review_session(a.session,a.max_gap_ms);payload=json.dumps(result,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\n",encoding="utf-8");print(f"Temporal report written: {a.output}")
        else:print(payload)
        return 1 if result["summary"]["invalid_captures"] else 0
    except (OSError,ValueError,KeyError,TemporalError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
