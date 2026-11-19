#!/usr/bin/env python3
"""Validate paired RGM captures and run exploratory labeled fingerprint trials."""
from __future__ import annotations
import argparse, hashlib, itertools, json, sys
from pathlib import Path
from typing import Any
try:
    from .rgm_snapshot_analyzer import parse_snapshot, SnapshotError
    from .rgm_graphics_comparator import decode_rgba, ImageError
    from .rgm_room_fingerprint import extract_cells, compare_fingerprints, FingerprintError
except ImportError:
    from rgm_snapshot_analyzer import parse_snapshot, SnapshotError
    from rgm_graphics_comparator import decode_rgba, ImageError
    from rgm_room_fingerprint import extract_cells, compare_fingerprints, FingerprintError

class CaptureValidationError(Exception): pass

def safe_child(root: Path, value: str, field: str) -> Path:
    if not isinstance(value,str) or not value: raise CaptureValidationError(f"{field} must be a relative path")
    p=(root/value).resolve(); base=root.resolve()
    if p != base and base not in p.parents: raise CaptureValidationError(f"{field} escapes capture directory")
    return p

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def inspect_capture(directory: Path) -> dict[str,Any]:
    mp=directory/"capture_metadata.json"
    if not mp.is_file(): return {"capture_directory":str(directory),"status":"invalid","errors":["metadata missing"]}
    errors=[]; warnings=[]
    try: m=json.loads(mp.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: return {"capture_directory":str(directory),"status":"invalid","errors":[str(e)]}
    if m.get("schema_version")!=1: errors.append("schema_version must be 1")
    for k in ("capture_id","session_id"):
        if not isinstance(m.get(k),str) or not m[k]: errors.append(f"{k} missing")
    if directory.name.startswith("FP-") and isinstance(m.get("capture_id"),str):
        if directory.name not in ("FP-"+m["capture_id"],m["capture_id"]):
            errors.append("capture_id does not match FP directory name")
    if directory.parent.name.startswith("SESSION-") and m.get("session_id") != directory.parent.name:
        errors.append("session_id does not match parent session directory")
    observed=m.get("observed") if isinstance(m.get("observed"),dict) else {}
    for k in ("location_label","activity"):
        if not isinstance(observed.get(k),str) or not observed[k]: errors.append(f"observed.{k} missing")
    cap=m.get("capture") if isinstance(m.get("capture"),dict) else {}
    paths={}
    for k in ("state_file","state_summary","graphics_directory"):
        try: paths[k]=safe_child(directory,cap.get(k),f"capture.{k}")
        except CaptureValidationError as e: errors.append(str(e))
    state=None
    if "state_file" in paths:
        try: state=parse_snapshot(paths["state_file"])
        except (OSError,SnapshotError) as e: errors.append(f"invalid state snapshot: {e}")
    if "state_summary" in paths:
        if not paths["state_summary"].is_file(): errors.append("state summary missing")
        else:
            try:
                summary=paths["state_summary"].read_text(encoding="utf-8",errors="replace")
                if not summary.strip(): errors.append("state summary is empty")
                elif "ROM_BANK" not in summary and "rom_bank" not in summary: warnings.append("state summary has no ROM bank field")
            except OSError as e: errors.append(f"cannot read state summary: {e}")
    graphics=paths.get("graphics_directory")
    if graphics and not graphics.is_dir(): errors.append("graphics directory missing")
    elif graphics and graphics.is_dir():
        for name,expected in (("map_9800.png",(256,256)),("map_9c00.png",(256,256)),("framebuffer.png",(160,144))):
            p=graphics/name
            if not p.is_file(): errors.append(f"graphics file missing: {name}"); continue
            try:
                im=decode_rgba(p)
                if (im["width"],im["height"])!=expected: errors.append(f"{name}: expected {expected[0]}x{expected[1]}")
            except (OSError,ImageError) as e: errors.append(f"{name}: {e}")
        manifest=graphics/"manifest.txt"
        if not manifest.is_file(): errors.append("graphics file missing: manifest.txt")
        else:
            try:
                manifest_text=manifest.read_text(encoding="utf-8",errors="replace")
                if not manifest_text.strip(): errors.append("graphics manifest is empty")
            except OSError as e: errors.append(f"cannot read graphics manifest: {e}")
    checks=m.get("source_sha256")
    if not isinstance(checks,dict) or not checks: warnings.append("source_sha256 absent; integrity not fully recorded")
    else:
        for rel,digest in checks.items():
            try:
                p=safe_child(directory,rel,"source_sha256 path")
                if not p.is_file(): errors.append(f"checksum source missing: {rel}")
                elif not isinstance(digest,str) or sha256_file(p).lower()!=digest.lower(): errors.append(f"SHA-256 mismatch: {rel}")
            except (OSError,CaptureValidationError) as e: errors.append(str(e))
    return {"capture_directory":str(directory),"capture_id":m.get("capture_id"),"session_id":m.get("session_id"),
            "experiment_id":m.get("experiment_id"),"checkpoint":m.get("checkpoint"),"repeat":m.get("repeat"),
            "status":"invalid" if errors else "valid","observed":observed,"errors":errors,"warnings":warnings,
            "state_sha256":state["sha256"] if state else None,"graphics_directory":str(graphics) if graphics else None}

def run_dataset(dataset:Path,max_shift:int=8,min_overlap:int=96)->dict[str,Any]:
    if not dataset.is_dir(): raise CaptureValidationError(f"dataset directory not found: {dataset}")
    dirs=sorted(p.parent for p in dataset.glob("SESSION-*/FP-*/capture_metadata.json"))
    captures=[inspect_capture(p) for p in dirs]; fps={}
    for c in captures:
        if c["status"]!="valid": continue
        try: fps[c["capture_id"]]=extract_cells(Path(c["graphics_directory"])/"map_9800.png")
        except (OSError,ImageError,FingerprintError) as e: c["status"]="invalid"; c["errors"].append(f"fingerprint: {e}")
    valid=[c for c in captures if c["status"]=="valid" and c["capture_id"] in fps]
    trials=[]
    for a,b in itertools.combinations(valid,2):
        la=str(a["observed"].get("location_label","")).strip().casefold()
        lb=str(b["observed"].get("location_label","")).strip().casefold()
        if not la or not lb or la=="unknown" or lb=="unknown": continue
        trials.append({"capture_a":a["capture_id"],"capture_b":b["capture_id"],
          "label_relation":"same_observed_label" if la==lb else "different_observed_label",
          "observed_label_a":a["observed"].get("location_label"),"observed_label_b":b["observed"].get("location_label"),
          "result":compare_fingerprints(fps[a["capture_id"]],fps[b["capture_id"]],max_shift,min_overlap),
          "note":"Tester labels are exploratory grouping labels, not verified ground truth."})
    summary={"captures_total":len(captures),"captures_valid":sum(c["status"]=="valid" for c in captures),
      "captures_invalid":sum(c["status"]!="valid" for c in captures),"pair_trials":len(trials),
      "same_label_pairs":sum(t["label_relation"]=="same_observed_label" for t in trials),
      "different_label_pairs":sum(t["label_relation"]=="different_observed_label" for t in trials),
      "candidate_matches":sum(t["result"].get("status")=="candidate_match" for t in trials),
      "weak_candidates":sum(t["result"].get("status")=="weak_candidate" for t in trials),
      "insufficient_evidence":sum(t["result"].get("status")=="insufficient_evidence" for t in trials)}
    return {"schema_version":1,"tool":"RGM Capture Validation Harness","dataset":str(dataset),"summary":summary,
      "capture_checks":[{k:v for k,v in c.items()} for c in captures],"pair_trials":trials,
      "limitations":["No room ID is inferred or verified.","Tester labels are not ground truth.",
        "Only rendered map_9800 RGBA cells are scored; map_9c00 is integrity/dimension checked only.",
        "Thresholds require labeled real-game captures and negative controls."]}

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("dataset",type=Path)
    p.add_argument("--max-shift",type=int,default=8); p.add_argument("--min-overlap",type=int,default=96); p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        report=run_dataset(a.dataset,a.max_shift,a.min_overlap); payload=json.dumps(report,indent=2,ensure_ascii=False)
        if a.output: a.output.write_text(payload+"\n",encoding="utf-8"); print(f"Report written: {a.output}")
        else: print(payload)
        return 1 if report["summary"]["captures_invalid"] else 0
    except (OSError,ValueError,CaptureValidationError) as e: print(f"ERROR: {e}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
