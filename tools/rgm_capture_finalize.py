#!/usr/bin/env python3
"""Finalize an RGM capture bundle by hashing its immutable raw artifacts."""
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile
from pathlib import Path

class FinalizeError(Exception):pass

def sha256(path:Path)->str:
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()

def finalize_capture(folder:Path)->dict:
 folder=folder.resolve()
 meta_path=folder/"capture_metadata.json"
 try:meta=json.loads(meta_path.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError) as e:raise FinalizeError(f"cannot read metadata: {e}") from e
 cap=meta.get("capture")
 if not isinstance(cap,dict):raise FinalizeError("capture object missing")
 rels=[cap.get("state_file"),cap.get("state_summary")]
 gd=cap.get("graphics_directory")
 if not isinstance(gd,str) or not gd:raise FinalizeError("graphics_directory missing")
 rels.append(gd)
 files={}
 for rel in rels[:2]:
  if not isinstance(rel,str) or not rel:raise FinalizeError("state artifact path missing")
  raw=folder/rel
  if raw.is_symlink():raise FinalizeError(f"required state artifact is a symlink: {rel}")
  p=raw.resolve()
  if folder not in p.parents:raise FinalizeError(f"path escapes capture folder: {rel}")
  if not p.is_file():raise FinalizeError(f"required state artifact missing: {rel}")
  files[p.relative_to(folder).as_posix()]=p
 graphics=(folder/gd).resolve()
 if folder not in graphics.parents or not graphics.is_dir() or graphics.is_symlink():
  raise FinalizeError("graphics directory missing, unsafe or symlink")
 for p in sorted(graphics.rglob("*")):
  if p.is_symlink():raise FinalizeError(f"symlink in graphics directory: {p.relative_to(folder)}")
  if p.is_file():files[p.relative_to(folder).as_posix()]=p
 required={"framebuffer.png","map_9800.png","map_9c00.png","manifest.txt"}
 found={Path(k).name for k in files if k.startswith(gd.rstrip("/")+"/")}
 missing=sorted(required-found)
 if missing:raise FinalizeError("required graphics files missing: "+", ".join(missing))
 if not files:raise FinalizeError("no raw artifacts found")
 meta["source_sha256"]={rel:sha256(path) for rel,path in sorted(files.items())}
 fd,tmp=tempfile.mkstemp(prefix="capture_metadata.",suffix=".tmp",dir=folder)
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as out:
   json.dump(meta,out,indent=2,ensure_ascii=False);out.write("\n");out.flush();os.fsync(out.fileno())
  os.replace(tmp,meta_path)
 except Exception:
  try:os.unlink(tmp)
  except OSError:pass
  raise
 return {"capture_id":meta.get("capture_id"),"artifact_count":len(files),"checksum_count":len(meta["source_sha256"]),
         "capture_dir":str(folder),"status":"finalized"}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("capture_dir",type=Path);a=p.parse_args()
 try:print(json.dumps(finalize_capture(a.capture_dir),indent=2,ensure_ascii=False));return 0
 except (OSError,ValueError,FinalizeError) as e:print(f"ERROR: {e}",file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
