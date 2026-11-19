import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "integration/regaiden-recomp/apply_rgm_adapter.py"

MAIN = """#include "audio_stats.h"
int main(int argc, char** argv) {
    const char* state_dump_file = NULL;
    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--rom") == 0 && i + 1 < argc) {
            explicit_rom_path = argv[++i];
        } else if (strcmp(argv[i], "--trace") == 0) {
        }
    }
    if (!rom_loader_acquire_rom(explicit_rom_path)) {
        return 1;
    }
#ifdef GBRT_ENABLE_PORT_MODULE
            gbrt_port_render(ctx, 1280, 720);
#endif
            const uint32_t* fb = gb_get_framebuffer(ctx);
}
"""

CMAKE = """add_library(gbrt STATIC
    ${CMAKE_CURRENT_SOURCE_DIR}/state_dump.c
    ${CMAKE_CURRENT_SOURCE_DIR}/asset_dump.c
)
"""

class UpstreamIntegrationTests(unittest.TestCase):
    def make_checkout(self, root, main=MAIN):
        src = root / "src/recompiled"
        src.mkdir(parents=True)
        (src / "Resident_Evil_Gaiden__USA__main.c").write_text(main)
        (src / "CMakeLists.txt").write_text(CMAKE)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return src

    def apply(self, root, force=True):
        args = [sys.executable, str(SCRIPT), str(root)]
        if force:
            args.append("--force-commit")
        return subprocess.run(args, text=True, capture_output=True)

    def test_successful_integration_is_opt_in_and_idempotence_guarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "upstream"
            src = self.make_checkout(root)
            result = self.apply(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            main = (src / "Resident_Evil_Gaiden__USA__main.c").read_text()
            cmake = (src / "CMakeLists.txt").read_text()
            self.assertIn("--rgm-capture-dir", main)
            self.assertIn("rgm_capture_pending", main)
            self.assertIn("rgm_capture_bundle.cpp", cmake)
            self.assertTrue((src / "rgm_capture_bundle.cpp").is_file())
            again = self.apply(root)
            self.assertNotEqual(again.returncode, 0)
            self.assertIn("marker already exists", again.stderr)

    def test_missing_anchor_does_not_partially_modify_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "upstream"
            bad_main = MAIN.replace('        } else if (strcmp(argv[i], "--trace") == 0) {\n        }\n', "")
            src = self.make_checkout(root, bad_main)
            before_main = (src / "Resident_Evil_Gaiden__USA__main.c").read_bytes()
            before_cmake = (src / "CMakeLists.txt").read_bytes()
            result = self.apply(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((src / "Resident_Evil_Gaiden__USA__main.c").read_bytes(), before_main)
            self.assertEqual((src / "CMakeLists.txt").read_bytes(), before_cmake)
            self.assertFalse((src / "rgm_capture_bundle.cpp").exists())

    def test_wrong_commit_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "upstream"
            src = self.make_checkout(root)
            result = self.apply(root, force=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("expected upstream", result.stderr)
            self.assertFalse((src / "rgm_capture_bundle.cpp").exists())

if __name__ == "__main__":
    unittest.main()
