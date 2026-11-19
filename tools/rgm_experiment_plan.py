#!/usr/bin/env python3
"""Generate an RGM-001E.9 controlled gameplay capture plan (no game data fabricated)."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path

def load_matrix(path:Path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema_version")!=1 or obj.get("milestone")!="RGM-001E.9":
        raise ValueError("unsupported experiment matrix schema/milestone")
    ids=[x.get("id") for x in obj.get("experiments",[])]
    if len(ids)!=len(set(ids)) or not ids: raise ValueError("experiment IDs must be non-empty and unique")
    for exp in obj["experiments"]:
        if not exp.get("captures") or len(exp["captures"])<2: raise ValueError(f"{exp.get('id')}: at least two capture checkpoints required")
    return obj

def safe_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}",value): raise ValueError("session ID may contain only letters, digits, _ and -")
    return value

def generate(matrix_path:Path,out:Path,session_id:str):
    matrix=load_matrix(matrix_path); safe_id(session_id)
    out.mkdir(parents=True,exist_ok=False)
    session={"schema_version":1,"session_id":session_id,"project":matrix["project"],"milestone":matrix["milestone"],
      "upstream":matrix["upstream"],"protocol":matrix["protocol"],"experiments":[]}
    for exp in matrix["experiments"]:
        e_dir=out/exp["id"];e_dir.mkdir()
        planned={"experiment_id":exp["id"],"name":exp["name"],"target":exp["target"],"question":exp["question"],
          "sequence":exp["sequence"],"capture_checkpoints":[]}
        for index,checkpoint in enumerate(exp["captures"],1):
            cid=f'{exp["id"]}-CP-{index:02d}'
            planned["capture_checkpoints"].append({"capture_id":cid,"checkpoint":checkpoint,"status":"not_captured",
              "required_files":["state_dump .bin",".txt summary","asset_dump graphics directory","capture_metadata.json"]})
            (e_dir/f"{cid}.json").write_text(json.dumps({"schema_version":1,"session_id":session_id,
              "capture_id":cid,"experiment_id":exp["id"],"checkpoint":checkpoint,
              "observed":{"location_label":"unknown","activity":"unknown","character":"unknown","speaker":"unknown"},
              "capture":{"state_file":"state.bin","state_summary":"state.txt","graphics_directory":"graphics"},
              "verification":{"room_identity":"unverified","scene_identity":"unverified","active_character":"unverified","speaker":"unverified"},
              "source_sha256":{}},indent=2)+"\\n",encoding="utf-8")
        session["experiments"].append(planned)
    (out/"session_plan.json").write_text(json.dumps(session,indent=2)+"\\n",encoding="utf-8")
    return {"session_directory":str(out),"experiments":len(session["experiments"]),
      "planned_capture_checkpoints":sum(len(x["capture_checkpoints"]) for x in session["experiments"]),
      "created_capture_metadata_templates":sum(len(x["capture_checkpoints"]) for x in session["experiments"]),
      "game_data_created":False,"note":"Templates only. No state snapshots or graphics captures are fabricated."}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--matrix",type=Path,default=Path("docs/analysis/RGM-001E.9-EXPERIMENT-MATRIX.json"))
    p.add_argument("--output",type=Path,required=True);p.add_argument("--session-id",required=True);a=p.parse_args()
    try: print(json.dumps(generate(a.matrix,a.output,a.session_id),indent=2));return 0
    except (OSError,ValueError,json.JSONDecodeError) as e: print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
