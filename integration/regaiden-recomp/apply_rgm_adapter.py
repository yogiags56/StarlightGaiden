#!/usr/bin/env python3
"""Apply the staged RGM capture adapter to an exact local upstream checkout.

Android builds expose a touch-menu capture request and neutral placeholder labels;
operators must annotate observed scene identity after exporting the bundle.
"""
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
    android_cmake_path = upstream / "android/app/jni/CMakeLists.txt"
    platform_header_path = upstream / "src/recompiled/runtime/include/platform_sdl.h"
    platform_cpp_path = upstream / "src/recompiled/runtime/src/platform_sdl.cpp"
    main_text, cmake_text = main_path.read_text(), cmake_path.read_text()
    android_cmake_text = android_cmake_path.read_text()
    platform_header_text = platform_header_path.read_text()
    platform_cpp_text = platform_cpp_path.read_text()
    if any(MARKER in value for value in
           (main_text, cmake_text, android_cmake_text, platform_header_text, platform_cpp_text)):
        raise RuntimeError("RGM adapter integration marker already exists; refusing duplicate patch")
    adapter_dir = upstream / "src/recompiled"
    if ((adapter_dir / "rgm_capture_bundle.h").exists() or
            (adapter_dir / "rgm_capture_bundle.cpp").exists()):
        raise RuntimeError("adapter destination already exists; refusing to overwrite local files")

    cmake_text = replace_once(
        cmake_text,
        "    ${CMAKE_CURRENT_SOURCE_DIR}/asset_dump.c\n",
        "    ${CMAKE_CURRENT_SOURCE_DIR}/asset_dump.c\n"
        "    ${CMAKE_CURRENT_SOURCE_DIR}/rgm_capture_bundle.cpp # " + MARKER + "\n",
        "CMake source list")
    android_cmake_text = replace_once(
        android_cmake_text,
        "    ${RECOMPILED_DIR}/asset_dump.c\n",
        "    ${RECOMPILED_DIR}/asset_dump.c\n"
        "    ${RECOMPILED_DIR}/rgm_capture_bundle.cpp # " + MARKER + "\n",
        "Android CMake source list")

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
        '    bool rgm_capture_pending = false;\n'
        '    bool rgm_android_auto_capture_path = false;\n',
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
        '#ifdef __ANDROID__\n'
        '    if (!rgm_capture_dir) {\n'
        '        rgm_session = "SESSION-ANDROID-0001";\n'
        '        rgm_experiment = "ANDROID-TOUCH-001";\n'
        '        rgm_checkpoint = "UNLABELED";\n'
        '        rgm_location = "unlabeled";\n'
        '        rgm_activity = "unclassified";\n'
        '        rgm_character = "unknown";\n'
        '        rgm_speaker = "unknown";\n'
        '    }\n'
        '#endif\n'
        '    if (rgm_capture_dir) {\n'
        '        if (!rgm_session || !rgm_capture_id || !rgm_experiment || !rgm_checkpoint || !rgm_location || !rgm_activity) {\n'
        '            fprintf(stderr, "RGM capture requires --rgm-session, --rgm-capture-id, --rgm-experiment, --rgm-checkpoint, --rgm-location and --rgm-activity\\n"); return 1;\n'
        '        }\n'
        '    }\n'
        '    if (!rom_loader_acquire_rom(explicit_rom_path)) {\n',
        "RGM CLI validation")
    main_text = replace_once(
        main_text,
        '            gbrt_port_render(ctx, 1280, 720);\n#endif\n            const uint32_t* fb = gb_get_framebuffer(ctx);\n',
        '            gbrt_port_render(ctx, 1280, 720);\n#endif\n'
        '            if (gb_platform_consume_rgm_capture_request()) {\n'
        '#ifdef __ANDROID__\n'
        '                static unsigned rgm_android_capture_serial = 0;\n'
        '                static char rgm_android_capture_dir[1024] = {};\n'
        '                static char rgm_android_capture_id[64] = {};\n'
        '                const char* rgm_external = SDL_AndroidGetExternalStoragePath();\n'
        '                if (!rgm_capture_dir && rgm_external && rgm_external[0]) {\n'
        '                    ++rgm_android_capture_serial;\n'
        '                    snprintf(rgm_android_capture_id, sizeof(rgm_android_capture_id), "ANDROID-%06u", rgm_android_capture_serial);\n'
        '                    snprintf(rgm_android_capture_dir, sizeof(rgm_android_capture_dir), "%s/snapshots/rgm/%s/FP-%s", rgm_external, rgm_session, rgm_android_capture_id);\n'
        '                    rgm_capture_id = rgm_android_capture_id;\n'
        '                    rgm_capture_dir = rgm_android_capture_dir;\n'
        '                    rgm_android_auto_capture_path = true;\n'
        '                }\n'
        '#endif\n'
        '                if (rgm_capture_dir && rgm_session && rgm_experiment && rgm_checkpoint && rgm_location && rgm_activity) {\n'
        '                    rgm_capture_pending = true;\n'
        '                    fprintf(stderr, "[RGM] Capture requested at completed frame %llu\\n", frame_index);\n'
        '                } else {\n'
        '                    fprintf(stderr, "[RGM] Capture request ignored: capture path/metadata unavailable\\n");\n'
        '                }\n'
        '            }\n'
        '            if (rgm_capture_pending) {\n'
        '                char rgm_status[512] = {};\n'
        '                const bool rgm_ok = rgm_capture_bundle(ctx, rgm_capture_dir, rgm_session, rgm_capture_id, rgm_experiment, rgm_checkpoint, rgm_repeat, rgm_location, rgm_activity, rgm_character, rgm_speaker, rgm_status, sizeof(rgm_status));\n'
        '                fprintf(stderr, "[RGM] %s\\n", rgm_status[0] ? rgm_status : (rgm_ok ? "capture complete" : "capture failed"));\n'
        '                rgm_capture_pending = false;\n'
        '#ifdef __ANDROID__\n'
        '                if (rgm_android_auto_capture_path) {\n'
        '                    rgm_capture_dir = NULL;\n'
        '                    rgm_capture_id = NULL;\n'
        '                    rgm_android_auto_capture_path = false;\n'
        '                }\n'
        '#endif\n'
        '            }\n'
        '            const uint32_t* fb = gb_get_framebuffer(ctx);\n',
        "post-frame capture hook")

    platform_header_text = replace_once(
        platform_header_text,
        "bool gb_platform_poll_events(GBContext* ctx);\n",
        "bool gb_platform_poll_events(GBContext* ctx);\n"
        "/* Consume one touch-menu capture request after a completed guest frame. */\n"
        "bool gb_platform_consume_rgm_capture_request(void); // " + MARKER + "\n",
        "SDL platform header API")
    platform_cpp_text = replace_once(
        platform_cpp_text,
        "static GBContext* g_registered_ctx = NULL;\n",
        "static GBContext* g_registered_ctx = NULL;\n"
        "static bool g_rgm_capture_requested = false; // " + MARKER + "\n",
        "SDL global capture request state")
    platform_cpp_text = replace_once(
        platform_cpp_text,
        "                if (ImGui::Button(\"Capture State Snapshot\", ImVec2(280.0f * ui_scale, 36.0f * ui_scale))) {\n"
        "                    capture_guest_snapshot(NULL);\n"
        "                }\n",
        "                if (ImGui::Button(\"Capture State Snapshot\", ImVec2(280.0f * ui_scale, 36.0f * ui_scale))) {\n"
        "                    capture_guest_snapshot(NULL);\n"
        "                }\n"
        "                if (ImGui::Button(\"Request RGM Bundle Capture\", ImVec2(280.0f * ui_scale, 36.0f * ui_scale))) {\n"
        "                    g_rgm_capture_requested = true;\n"
        "                }\n",
        "touch-accessible RGM capture button")
    if "bool gb_platform_consume_rgm_capture_request(void)" in platform_cpp_text:
        raise RuntimeError("SDL capture request consumer already exists")
    platform_cpp_text += (
        "\n\n/* " + MARKER + " */\n"
        "bool gb_platform_consume_rgm_capture_request(void) {\n"
        "    const bool requested = g_rgm_capture_requested;\n"
        "    g_rgm_capture_requested = false;\n"
        "    return requested;\n"
        "}\n"
    )

    # All textual anchors are validated before any upstream file is modified.
    shutil.copy2(here / "integration/regaiden-recomp/rgm_capture_bundle.h",
                 adapter_dir / "rgm_capture_bundle.h")
    shutil.copy2(here / "integration/regaiden-recomp/rgm_capture_bundle.cpp",
                 adapter_dir / "rgm_capture_bundle.cpp")
    cmake_path.write_text(cmake_text)
    android_cmake_path.write_text(android_cmake_text)
    main_path.write_text(main_text)
    platform_header_path.write_text(platform_header_text)
    platform_cpp_path.write_text(platform_cpp_text)
    print("Applied RGM capture adapter integration.")
    print(f"Upstream commit: {head}")
    print("Desktop: use --rgm-capture-* metadata options. Desktop and Android: request capture from the Diagnostics menu.")
    return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
