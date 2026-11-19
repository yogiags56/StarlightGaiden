import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "tools" / "rgm_snapshot_analyzer.py"
MAGIC = b"REGAIDEN-SNAPSHOT-1\0"
SIZES = (0x8000, 0x7F, 0x80, 0xA0)


def write_snapshot(path, edits=(), endian="<"):
    blocks = [bytearray(size) for size in SIZES]
    for block_index, offset, value in edits:
        blocks[block_index][offset] = value
    path.write_bytes(MAGIC + struct.pack(endian + "4I", *SIZES) + b"".join(blocks))


class SnapshotAnalyzerTests(unittest.TestCase):
    def test_diff_and_bank_accounting(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a, b, report = root / "a.bin", root / "b.bin", root / "report.json"
            write_snapshot(a)
            write_snapshot(b, [(0, 0x123, 7), (2, 0x40, 1), (3, 2, 9)])
            result = subprocess.run(
                [sys.executable, str(ANALYZER), str(a), str(b), "--output", str(report)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(report.read_text())
            self.assertEqual(data["comparison"]["summary"], {
                "changed_wram_bytes": 1, "changed_hram_bytes": 0,
                "changed_io_bytes": 1, "changed_oam_bytes": 1})
            self.assertEqual(data["comparison"]["wram_bank_changes"][0]["changed_bytes"], 1)

    def test_reject_bad_magic(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.bin"
            bad.write_bytes(b"not a snapshot")
            result = subprocess.run(
                [sys.executable, str(ANALYZER), str(bad)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("magic/header", result.stderr)

    def test_reject_trailing_data(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "trailing.bin"
            write_snapshot(bad)
            bad.write_bytes(bad.read_bytes() + b"x")
            result = subprocess.run(
                [sys.executable, str(ANALYZER), str(bad)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("byte tambahan", result.stderr)


if __name__ == "__main__":
    unittest.main()
