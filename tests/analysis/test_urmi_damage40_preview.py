"""NEW synthetic complete-prefix controls only; no saved/native run or render."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / "scripts/preview-urmi-damage40.py"
SPEC = importlib.util.spec_from_file_location("urmi_preview_controls", SOURCE)
PREVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREVIEW)


class CompletedPrefixControls(unittest.TestCase):
    def test_exact_raw_prefix_ignores_unfinished_future_tail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / "active.csv", root / "copied.csv"
            prefix = (b"frame,particle_id,value\r\n"
                      b"0,0,1.25d0\r\n0,1,2.5D0\r\n"
                      b"1,0,3.75d0\r\n1,1,4.0d0\r\n")
            source.write_bytes(prefix + b"2,0,5.0d0\r\n2,1,")
            binding = PREVIEW.copy_csv_prefix(source, target, 2, particles=2)
            self.assertEqual(target.read_bytes(), prefix)
            self.assertTrue(source.read_bytes().endswith(b"2,1,"))
            self.assertEqual(binding["dataRows"], 4)
            self.assertEqual(binding["prefixSha256Before"], binding["prefixSha256After"])

    def test_rejects_selected_unfinished_line_and_wrong_particle_order(self):
        fixtures = [b"frame,particle_id,value\n0,0,1\n0,1,2",
                    b"frame,particle_id,value\n0,0,1\n0,0,2\n"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, raw in enumerate(fixtures):
                source = root / f"bad-{index}.csv"
                source.write_bytes(raw)
                with self.assertRaises(ValueError):
                    PREVIEW.copy_csv_prefix(source, root / f"retained-copy-{index}.csv", 1, particles=2)
                self.assertEqual(source.read_bytes(), raw)

    def test_not_ready_creates_no_preview_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run, output = root / "run", root / "must-not-exist"
            run.mkdir()
            manifest = {"scenario": "urmi-damage40", "status": "running", "complete": False,
                        "phase": "drained-ramp-and-relaxation", "savedFrames": 0, "particleCount": 6714}
            original = json.dumps(manifest).encode()
            (run / "manifest.json").write_bytes(original)
            arguments = [str(SOURCE), "--run-dir", str(run), "--output-dir", str(output), "--video"]
            stdout = io.StringIO()
            with patch.object(sys, "argv", arguments), contextlib.redirect_stdout(stdout):
                self.assertEqual(PREVIEW.main(), 0)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "NOT_READY")
            self.assertFalse(output.exists())
            self.assertEqual((run / "manifest.json").read_bytes(), original)
            manifest.update(phase="undrained-dynamic", savedFrames=5)
            self.assertIsNone(PREVIEW.preview_count(manifest))
            manifest["savedFrames"] = 6
            self.assertEqual(PREVIEW.preview_count(manifest), 6)
            manifest["savedFrames"] = 29
            self.assertEqual(PREVIEW.preview_count(manifest), 11)


if __name__ == "__main__":
    unittest.main()
