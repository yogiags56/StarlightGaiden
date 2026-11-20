#!/usr/bin/env python3
"""Conservative single-capture scene-state evidence classifier for RGM.

It emits evidence-backed candidates and explicit unknowns. It does not infer
combat, cutscene, active character, speaker, or UI subtype from unvalidated
memory addresses or music IDs.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any
try:
    from .rgm_capture_validator import inspect_capture
    from .rgm_snapshot_analyzer import parse_snapshot,SnapshotError
    from .rgm_scene_correlator import parse_summary
except ImportError:
    from rgm_capture_validator import inspect_capture
    from rgm_snapshot_analyzer import parse_snapshot,SnapshotError
    from rgm_scene_correlator import parse_summary

SCENE_TYPES=("exploration","dialogue","cutscene","inventory_pda","normal_combat","boss_combat","room_transition","save_load")
DIALOGUE_MIN_WY=72
DIALOGUE_MAX_WY=134

class SceneClassificationError(Exception): pass

def analyze_capture(directory:Path)->dict[str,Any]:
    checked=inspect_capture(directory)
    if checked.get("status")!="valid":
        raise SceneClassificationError("capture failed integrity validation: "+"; ".join(checked.get("errors",[])))
    meta=json.loads((directory/"capture_metadata.json").read_text(encoding="utf-8"))
    cap=meta["capture"]
    state=parse_snapshot(directory/cap["state_file"])
    summary=parse_summary(directory/cap["state_summary"])
    wram_bank=summary.get("wram_bank")
    # Upstream game_state.h explicitly maps SVBK 0 to bank 1; bank 2 is the
    # observed UI/menu family. This does not distinguish inventory/PDA/title/save.
    normalized_bank=1 if wram_bank==0 else wram_bank
    io=state["blocks"]["io"]
    lcdc=summary.get("lcdc",io[0x40])
    wy=summary.get("wy",io[0x4a])
    wx=summary.get("wx",io[0x4b])
    window_enabled=bool(lcdc & 0x20)
    ui_screen=(normalized_bank==2) if normalized_bank is not None else None
    dialogue_geometry=(window_enabled and wx is not None and wx<=166 and
                       wy is not None and DIALOGUE_MIN_WY<=wy<=DIALOGUE_MAX_WY)
    dialogue_candidate=bool(dialogue_geometry and ui_screen is False)
    features={
      "wram_bank_raw":wram_bank,"wram_bank_normalized":normalized_bank,
      "ui_bank2_indicator":ui_screen,
      "rom_bank":summary.get("rom_bank"),"program_counter":summary.get("pc"),
      "lcdc":lcdc,"window_enabled":window_enabled,"wx":wx,"wy":wy,
      "dialogue_window_geometry":bool(dialogue_geometry),
      "active_sprite_count":summary.get("active_sprite_count"),
      "music_track_hint":state["blocks"]["wram"][0x0e8c]
    }
    states={name:"unresolved" for name in SCENE_TYPES}
    candidates=[]
    if ui_screen is True:
        candidates.append({"type":"ui_screen_family","status":"candidate",
          "evidence":["wram_bank_2"],"subtype":"unresolved",
          "cannot_distinguish":["inventory","PDA","title_menu","save_menu","other_UI"]})
    elif dialogue_candidate:
        candidates.append({"type":"dialogue","status":"candidate",
          "evidence":["window_layer_enabled","window_x_within_screen","bottom_anchored_window_geometry","not_ui_bank"],
          "speaker":"unresolved"})
    else:
        candidates.append({"type":"unclassified","status":"insufficient_evidence",
          "evidence":[]})
    return {"schema_version":1,"tool":"RGM Scene State Classification Foundation",
      "capture_id":checked.get("capture_id"),"observed_metadata":meta.get("observed",{}),
      "features":features,"scene_type_states":states,"candidates":candidates,
      "identity":{"room_id":"unknown","active_character":"unknown","speaker":"unknown"},
      "confidence_policy":{"status":"candidate_or_unresolved_only",
        "note":"No calibrated probabilities are produced. Candidate rules are source-informed heuristics, not validated ground truth."},
      "limitations":[
        "WRAM bank 2 identifies a UI/menu family only; it cannot distinguish inventory, PDA, title menu or save menu.",
        "Dialogue geometry follows upstream hd_pack.c (WY 72..134, window enabled, WX <=166) and remains a heuristic.",
        "Exploration, cutscene, normal combat, boss combat, room transition and save/load have no validated single-capture discriminators yet.",
        "Music ID, ROM bank, PC and sprite count are contextual features, not unique scene identifiers.",
        "No active character or dialogue speaker is inferred."
      ]}

def run_dataset(dataset:Path)->dict[str,Any]:
    if not dataset.is_dir(): raise SceneClassificationError(f"dataset directory not found: {dataset}")
    files=sorted(dataset.glob("SESSION-*/FP-*/capture_metadata.json"))
    results=[];errors=[]
    for f in files:
        try: results.append(analyze_capture(f.parent))
        except (OSError,ValueError,KeyError,SnapshotError,SceneClassificationError) as e:
            errors.append({"capture_directory":str(f.parent),"error":str(e)})
    return {"schema_version":1,"tool":"RGM Scene State Classification Foundation",
      "summary":{"captures_found":len(files),"classified_candidates":len(results),
        "invalid_or_unreadable":len(errors),
        "dialogue_candidates":sum(any(c["type"]=="dialogue" for c in r["candidates"]) for r in results),
        "ui_screen_family_candidates":sum(any(c["type"]=="ui_screen_family" for c in r["candidates"]) for r in results),
        "unclassified":sum(any(c["type"]=="unclassified" for c in r["candidates"]) for r in results)},
      "captures":results,"errors":errors,
      "global_warning":"This is a conservative evidence classifier foundation, not a trained or calibrated gameplay scene classifier."}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("dataset",type=Path);p.add_argument("--output",type=Path)
    a=p.parse_args()
    try:
        report=run_dataset(a.dataset);payload=json.dumps(report,indent=2,ensure_ascii=False)
        if a.output:a.output.write_text(payload+"\n",encoding="utf-8");print(f"Report written: {a.output}")
        else:print(payload)
        return 1 if report["summary"]["invalid_or_unreadable"] else 0
    except (OSError,ValueError,SceneClassificationError) as e:
        print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
