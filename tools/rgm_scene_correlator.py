#!/usr/bin/env python3
"""Correlate RGM map, memory, execution, camera, sprite and audio evidence.
Reports pairwise evidence only; never assigns room, scene, character or speaker IDs."""
from __future__ import annotations
import argparse,json,re,sys,itertools
from pathlib import Path
from typing import Any
try:
 from .rgm_capture_validator import inspect_capture
 from .rgm_snapshot_analyzer import parse_snapshot,SnapshotError
 from .rgm_room_fingerprint import extract_cells,compare_fingerprints,FingerprintError
 from .rgm_graphics_comparator import ImageError
except ImportError:
 from rgm_capture_validator import inspect_capture
 from rgm_snapshot_analyzer import parse_snapshot,SnapshotError
 from rgm_room_fingerprint import extract_cells,compare_fingerprints,FingerprintError
 from rgm_graphics_comparator import ImageError

class CorrelationError(Exception): pass
MUSIC_OFFSET=0x0E8C
def parse_summary(path):
 if not path or not path.is_file(): return {}
 t=path.read_text(encoding="utf-8",errors="replace"); out={}
 pats={"label":r"^label=(.*)$","rom_bank":r"^rom_bank=(\d+)$","wram_bank":r"^wram_bank=(\d+)$",
 "pc":r"^pc=([0-9A-Fa-f]{1,4})\s+sp=[0-9A-Fa-f]{1,4}$","sp":r"^pc=[0-9A-Fa-f]{1,4}\s+sp=([0-9A-Fa-f]{1,4})$",
 "lcdc":r"^LCDC\(FF40\)=([0-9A-Fa-f]{2})","stat":r"^LCDC\(FF40\)=[0-9A-Fa-f]{2}\s+STAT\(FF41\)=([0-9A-Fa-f]{2})",
 "scy":r"^SCY\(FF42\)=([0-9A-Fa-f]{2})","scx":r"^SCY\(FF42\)=[0-9A-Fa-f]{2}\s+SCX\(FF43\)=([0-9A-Fa-f]{2})",
 "ly":r"^SCY\(FF42\)=[0-9A-Fa-f]{2}\s+SCX\(FF43\)=[0-9A-Fa-f]{2}\s+LY\(FF44\)=([0-9A-Fa-f]{2})",
 "wy":r"^WY\(FF4A\)=([0-9A-Fa-f]{2})","wx":r"^WY\(FF4A\)=[0-9A-Fa-f]{2}\s+WX\(FF4B\)=([0-9A-Fa-f]{2})",
 "active_sprite_count":r"^active_sprite_count=(\d+)$"}
 for k,p in pats.items():
  m=re.search(p,t,re.M)
  if m: out[k]=m.group(1) if k=="label" else int(m.group(1),10 if k=="active_sprite_count" else 16)
 out["active_sprites"]=[{"index":int(m[1]),"y":int(m[2]),"x":int(m[3]),"tile":int(m[4],16),"flags":int(m[5],16)}
  for m in re.findall(r"^obj(\d+)\s+y=\s*(\d+)\s+x=\s*(\d+)\s+tile=([0-9A-Fa-f]{2})\s+flags=([0-9A-Fa-f]{2})$",t,re.M)]
 return out
def byte_delta(a,b):
 if a is None or b is None:return None
 d=(b-a)&255;return min(d,256-d)
def memory_profile(a,b):
 out={}
 for n in ("wram","hram","io","oam"):
  x,y=a["blocks"][n],b["blocks"][n]; c=sum(i!=j for i,j in zip(x,y))
  out[n]={"changed_bytes":c,"total_bytes":len(x),"changed_ratio":c/len(x)}
 out["wram_banks"]=[{"bank":i,"changed_bytes":sum(x!=y for x,y in zip(a["blocks"]["wram"][i*4096:(i+1)*4096],b["blocks"]["wram"][i*4096:(i+1)*4096]))} for i in range(8)]
 out["note"]="Memory deltas describe state change; large deltas do not by themselves imply a different room."
 return out
def correlate(a,b,max_shift=8,min_overlap=96):
 da,db=Path(a["graphics_directory"]),Path(b["graphics_directory"])
 ma=json.loads((Path(a["capture_directory"])/"capture_metadata.json").read_text())
 mb=json.loads((Path(b["capture_directory"])/"capture_metadata.json").read_text())
 sa=parse_snapshot(Path(a["capture_directory"])/ma["capture"]["state_file"])
 sb=parse_snapshot(Path(b["capture_directory"])/mb["capture"]["state_file"])
 xa=parse_summary(Path(a["capture_directory"])/ma["capture"]["state_summary"])
 xb=parse_summary(Path(b["capture_directory"])/mb["capture"]["state_summary"])
 ta,tb=sa["blocks"]["wram"][MUSIC_OFFSET],sb["blocks"]["wram"][MUSIC_OFFSET]
 xa["music_track"]=ta if ta<=27 else None;xb["music_track"]=tb if tb<=27 else None
 maps={n:compare_fingerprints(extract_cells(da/n),extract_cells(db/n),max_shift,min_overlap) for n in ("map_9800.png","map_9c00.png")}
 scores=[v["best_alignment"]["weighted_similarity"] for v in maps.values() if v.get("best_alignment") and v.get("status")!="insufficient_evidence"]
 map_score=sum(scores)/len(scores) if scores else None
 sa_set={(x["index"],x["y"],x["x"],x["tile"],x["flags"]) for x in xa.get("active_sprites",[])}
 sb_set={(x["index"],x["y"],x["x"],x["tile"],x["flags"]) for x in xb.get("active_sprites",[])}
 union=sa_set|sb_set; sprite_j=len(sa_set&sb_set)/len(union) if union else 1.0
 runtime={"rom_bank":{"a":xa.get("rom_bank"),"b":xb.get("rom_bank"),"same":xa.get("rom_bank")==xb.get("rom_bank") if "rom_bank" in xa and "rom_bank" in xb else None},
 "wram_bank":{"a":xa.get("wram_bank"),"b":xb.get("wram_bank"),"same":xa.get("wram_bank")==xb.get("wram_bank") if "wram_bank" in xa and "wram_bank" in xb else None},
 "pc":{"a":xa.get("pc"),"b":xb.get("pc"),"same":xa.get("pc")==xb.get("pc") if "pc" in xa and "pc" in xb else None},
 "camera_delta_pixels":{"dx":byte_delta(xa.get("scx"),xb.get("scx")),"dy":byte_delta(xa.get("scy"),xb.get("scy"))},
 "sprite_summary":{"count_a":len(sa_set),"count_b":len(sb_set),"exact_sprite_jaccard":sprite_j},
 "music_track":{"a":xa["music_track"],"b":xb["music_track"],"same":xa["music_track"]==xb["music_track"] if xa["music_track"] is not None and xb["music_track"] is not None else None,
 "interpretation":"Weak context hint only; music may persist across scene/UI changes."}}
 corroborators=[]
 if runtime["rom_bank"]["same"] is True:corroborators.append("same_rom_bank")
 if runtime["wram_bank"]["same"] is True:corroborators.append("same_wram_bank")
 if sprite_j>=.5:corroborators.append("sprite_overlap")
 if runtime["music_track"]["same"] is True:corroborators.append("same_music_track")
 status="strong_correlation_candidate" if map_score is not None and map_score>=.82 and corroborators else ("weak_correlation_candidate" if map_score is not None and map_score>=.60 else "insufficient_evidence")
 oam_a,oam_b=sa["blocks"]["oam"],sb["blocks"]["oam"]; changed=sum(x!=y for x,y in zip(oam_a,oam_b))
 return {"capture_a":a["capture_id"],"capture_b":b["capture_id"],"observed_labels":[a["observed"].get("location_label"),b["observed"].get("location_label")],
 "status":status,"environment":{"map_comparisons":maps,"mean_available_map_similarity":map_score},"runtime_context":runtime,
 "memory_transition":memory_profile(sa,sb),"oam_binary_comparison":{"changed_bytes":changed,"total_bytes":160,"byte_similarity":1-changed/160},
 "corroborating_signals":corroborators,"limitations":["Correlation candidate only; no room/scene/character/speaker identity is assigned.",
 "ROM bank, PC, WRAM bank, OAM and music can vary within a room or persist across scene changes.",
 "Map fingerprints use rendered RGBA and provisional thresholds; real-game calibration is required."]}
def run_dataset(dataset,max_shift=8,min_overlap=96):
 if not dataset.is_dir():raise CorrelationError(f"dataset directory not found: {dataset}")
 captures=[]
 for p in sorted(dataset.glob("SESSION-*/FP-*/capture_metadata.json")):
  c=inspect_capture(p.parent)
  if c["status"]=="valid":c["capture_directory"]=str(p.parent);captures.append(c)
 pairs=[correlate(x,y,max_shift,min_overlap) for x,y in itertools.combinations(captures,2)]
 return {"schema_version":1,"tool":"RGM Multi-Signal Scene Correlator","dataset":str(dataset),
 "summary":{"valid_captures":len(captures),"pair_correlations":len(pairs),
 "strong_correlation_candidates":sum(x["status"]=="strong_correlation_candidate" for x in pairs),
 "weak_correlation_candidates":sum(x["status"]=="weak_correlation_candidate" for x in pairs),
 "insufficient_evidence":sum(x["status"]=="insufficient_evidence" for x in pairs)},
 "pair_correlations":pairs,"global_warning":"Evidence correlation only; this does not certify rooms, scenes, characters or speakers."}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("dataset",type=Path);p.add_argument("--max-shift",type=int,default=8);p.add_argument("--min-overlap",type=int,default=96);p.add_argument("--output",type=Path);a=p.parse_args()
 try:
  r=run_dataset(a.dataset,a.max_shift,a.min_overlap);s=json.dumps(r,indent=2,ensure_ascii=False)
  if a.output:a.output.write_text(s+"\n",encoding="utf-8");print(f"Report written: {a.output}")
  else:print(s)
  return 0
 except (OSError,ValueError,KeyError,SnapshotError,ImageError,FingerprintError,CorrelationError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
