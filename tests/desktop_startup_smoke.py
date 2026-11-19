#!/usr/bin/env python3
"""Process-startup and opt-in RGM CLI smoke tests; deliberately no game ROM."""
import subprocess
import sys
import tempfile
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
if not exe.is_file():
    raise SystemExit(f"executable missing: {exe}")

with tempfile.TemporaryDirectory(prefix="rgm-desktop-smoke-") as td:
    root = Path(td)
    missing_rom = root / "no-such-rom.gbc"

    normal = subprocess.run(
        [str(exe), "--rom", str(missing_rom)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20,
    )
    if normal.returncode == 0:
        raise SystemExit("normal startup unexpectedly accepted a nonexistent ROM")
    if "Valid Resident Evil Gaiden (USA) GBC ROM was not provided" not in normal.stdout:
        raise SystemExit("normal startup did not reach the expected ROM validation failure:\n" + normal.stdout)
    if "[RGM]" in normal.stdout:
        raise SystemExit("ordinary startup unexpectedly invoked the RGM capture hook")

    capture = root / "SESSION-CI" / "FP-CAP-CI-001"
    opted = subprocess.run(
        [
            str(exe), "--rom", str(missing_rom),
            "--rgm-capture-dir", str(capture),
            "--rgm-session", "SESSION-CI",
            "--rgm-capture-id", "CAP-CI-001",
            "--rgm-experiment", "EXP-CI",
            "--rgm-checkpoint", "stationary",
            "--rgm-repeat", "1",
            "--rgm-location", "CI synthetic startup",
            "--rgm-activity", "exploration",
            "--rgm-character", "unknown",
            "--rgm-speaker", "unknown",
        ],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20,
    )
    if opted.returncode == 0:
        raise SystemExit("opt-in startup unexpectedly accepted a nonexistent ROM")
    if "RGM capture requires" in opted.stdout:
        raise SystemExit("valid RGM CLI arguments were not accepted:\n" + opted.stdout)
    if "Valid Resident Evil Gaiden (USA) GBC ROM was not provided" not in opted.stdout:
        raise SystemExit("opt-in startup did not reach expected ROM validation:\n" + opted.stdout)
    if capture.exists():
        raise SystemExit("capture directory created before a game frame existed")

print("Desktop process startup and RGM CLI smoke tests passed (no ROM/gameplay was run).")
