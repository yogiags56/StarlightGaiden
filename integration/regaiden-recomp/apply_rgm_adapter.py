#!/usr/bin/env python3
"""Apply the staged RGM capture adapter to an exact local upstream checkout."""
from __future__ import annotations
import argparse, shutil, subprocess, sys
from pathlib import Path

UPSTREAM_COMMIT = "e5befd20e67939d939319149d1c1177b8e6c5cd6"
MAIN = "src/recompiled/Resident_Evil_Gaiden__USA__main.c"
CMAKE = "src/recompiled/CMakeLists.txt"
MARKER = "RGM_CAPTURE_BUNDLE_INTEGRATION"

def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or "git command failed")
    return p.stdout.strip()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("upstream", type=Path, help="local regaiden-recomp checkout")
    ap.add_argument("--force-commit", action="store_true",
                    help="allow a different commit only after manual source review")
    args = ap.parse_args()
    here = Path(__file__).resolve().parents[2]
    upstream = args.upstream.resolve()
    if not (upstream / ".git").exists():
        raise RuntimeError("upstream path is not a Git checkout")
    head = git(upstream, "rev-parse", "HEAD")
    if head != UPSTREAM_COMMIT and not args.force_commit:
        raise RuntimeError(f"expected upstream {UPSTREAM_COMMIT}, found {head}; review source before --force-commit")
    main_path, cmake_path = upstream / MAIN, upstream / CMAKE
    main_text, cmake_text = main_path.read_text(), cmake_path.read_text()
    if MARKER in main_text or MARKER in cmake_text:
        raise RuntimeError("RGM adapter integration marker already exists; refusing duplicate patch")
    adapter_dir = upstream / "src/recompiled"
    shutil.copy2(here / "integration/regaiden-recomp/rgm_capture_bundle.h",
                 adapter_dir / "rgm_capture_bundle.h")
    shutil.copy2(here / "integration/regaiden-recomp/rgm_capture_bundle.cpp",
                 adapter_dir / "rgm_capture_bundle.cpp")

    cmake_text = replace_once(
        cmake_text,
        "    ${CMAKE_CURRENT_SOURCE_DIR}/asset_dump.c\n",
        "    ${CMAKE_CURRENT_SOURCE_DIR}/asset_dump.c\n"
        "    ${CMAKE_CURRENT_SOURCE_DIR}/rgm_capture_bundle.cpp # " + MARKER + "\n",
        "CMake source list")

    main_text = replace_once(
        main_text,
        '#include "audio_stats.h"\n',
        '#include "audio_stats.h"\n#include "rgm_capture_bundle.h" // ' + MARKER + '\n',
        "main include")
    main_text = replace_once(
        main_text,
        '    const char* state_dump_file = NULL;\n',
        '    const char* state_dump_file = NULL;\n'
        '    const char* rgm_capture_dir = NULL;\n'
        '    const char* rgm_session = NULL;\n'
        '    const char* rgm_capture_id = NULL;\n'
        '    const char* rgm_experiment = NULL;\n'
        '    const char* rgm_checkpoint = NULL;\n'
        '    const char* rgm_location = NULL;\n'
        '    const char* rgm_activity = NULL;\n'
        '    const char* rgm_character = NULL;\n'
        '    const char* rgm_speaker = NULL;\n'
        '    unsigned rgm_repeat = 1;\n'
        '    bool rgm_capture_pending = false;\n',
        "RGM CLI variables")
    main_text = replace_once(
        main_text,
        '        } else if (strcmp(argv[i], "--trace") == 0) {\n',
        '        } else if (strcmp(argv[i], "--rgm-capture-dir") == 0 && i + 1 < argc) {\n'
        '            rgm_capture_dir = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-session") == 0 && i + 1 < argc) {\n'
        '            rgm_session = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-capture-id") == 0 && i + 1 < argc) {\n'
        '            rgm_capture_id = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-experiment") == 0 && i + 1 < argc) {\n'
        '            rgm_experiment = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-checkpoint") == 0 && i + 1 < argc) {\n'
        '            rgm_checkpoint = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-repeat") == 0 && i + 1 < argc) {\n'
        '            char* end = NULL; unsigned long value = strtoul(argv[++i], &end, 10);\n'
        '            if (!end || *end || value == 0 || value > 1000000) { fprintf(stderr, "Invalid --rgm-repeat\\n"); return 1; }\n'
        '            rgm_repeat = (unsigned)value;\n'
        '        } else if (strcmp(argv[i], "--rgm-location") == 0 && i + 1 < argc) {\n'
        '            rgm_location = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-activity") == 0 && i + 1 < argc) {\n'
        '            rgm_activity = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-character") == 0 && i + 1 < argc) {\n'
        '            rgm_character = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--rgm-speaker") == 0 && i + 1 < argc) {\n'
        '            rgm_speaker = argv[++i];\n'
        '        } else if (strcmp(argv[i], "--trace") == 0) {\n',
        "RGM CLI parser")
    main_text = replace_once(
        main_text,
        '    if (!rom_loader_acquire_rom(explicit_rom_path)) {\n',
        '    if (rgm_capture_dir) {\n'
        '        if (!rgm_session || !rgm_capture_id || !rgm_experiment || !rgm_checkpoint || !rgm_location || !rgm_activity) {\n'
        '            fprintf(stderr, "RGM capture requires --rgm-session, --rgm-capture-id, --rgm-experiment, --rgm-checkpoint, --rgm-location and --rgm-activity\\n"); return 1;\n'
        '        }\n'
        '        rgm_capture_pending = true;\n'
        '    }\n'
        '    if (!rom_loader_acquire_rom(explicit_rom_path)) {\n',
        "RGM CLI validation")
    main_text = replace_once(
        main_text,
        '            gbrt_port_render(ctx, 1280, 720);\n#endif\n            const uint32_t* fb = gb_get_framebuffer(ctx);\n',
        '            gbrt_port_render(ctx, 1280, 720);\n#endif\n'
        '            if (rgm_capture_pending) {\n'
        '                char rgm_status[512] = {};\n'
        '                const bool rgm_ok = rgm_capture_bundle(ctx, rgm_capture_dir, rgm_session, rgm_capture_id, rgm_experiment, rgm_checkpoint, rgm_repeat, rgm_location, rgm_activity, rgm_character, rgm_speaker, rgm_status, sizeof(rgm_status));\n'
        '                fprintf(stderr, "[RGM] %s\\n", rgm_status[0] ? rgm_status : (rgm_ok ? "capture complete" : "capture failed"));\n'
        '                rgm_capture_pending = false;\n'
        '            }\n'
        '            const uint32_t* fb = gb_get_framebuffer(ctx);\n',
        "post-frame capture hook")
    cmake_path.write_text(cmake_text)
    main_path.write_text(main_text)
    print("Applied RGM capture adapter integration.")
    print(f"Upstream commit: {head}")
    print("Next: configure/build desktop; then run with --rgm-capture-* options.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
