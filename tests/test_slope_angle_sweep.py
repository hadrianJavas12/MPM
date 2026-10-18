#!/usr/bin/env python3
"""Pure Python contract checks for the no-notch paired-slope batch workflow."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweep_unnotched_slope import make_plan, case_content, prepare, verified_run, entries
from render_slope_montage import kappa_color, draw_panel
import numpy as np


class TestSlopeAngleSweep(unittest.TestCase):
    def options(self, **overrides):
        args = dict(angles=[45, 55, 65], height=12., base_height=4.,
                    shelf_aspect=4.0, runout_aspect=4.5, mesh_size=0.5,
                    mps_per_cell=2, frames=80, substeps=40, settle_steps=220,
                    cfl_scale=0.35, workers=2, parallel=1)
        args.update(overrides)
        return argparse.Namespace(**args)

    def test_pair_is_identical_except_constitutive_variant(self):
        plan = make_plan(self.options())
        h = case_content(55, "H", plan)
        hs = case_content(55, "HS", plan)
        for source in (h, hs):
            self.assertIn(":slope 55.00000000d0", source)
            self.assertIn(":notch-height 0d0", source)
            self.assertIn(":notch-depth 0d0", source)
            self.assertIn(":mesh-size 0.50000000d0", source)
            self.assertIn('(gethash "elongatedShelfAspect" params) 4.00000000d0', source)
            self.assertIn('(gethash "runoutAspect" params) 4.50000000d0', source)
            self.assertIn('(gethash "settleSteps" params) 220', source)
            self.assertIn('(gethash "cflScale" params) 0.35000000d0', source)
            self.assertIn(":frames 80", source)
            self.assertIn('(cl-mpm/models/mc-evolution:make-urmi-evolution-law', source)
            self.assertNotIn('(cl-mpm/models/mc-evolution:make-evolution-law', source)
            self.assertIn(":beta -5.0d0", source)
            self.assertIn(":postpeak-segments 8", source)
            self.assertIn(":residual-kappa 0.20d0", source)
            self.assertIn(":loading (make-loading :gravity)", source)
        self.assertIn(":material (make-material :mc-h\n", h)
        self.assertIn(":variant :h\n", h)
        self.assertIn(":material (make-material :mc-hs\n", hs)
        self.assertIn(":variant :hs\n", hs)
        self.assertEqual(h.replace(":mc-h", ":mc-hs").replace(":variant :h\n", ":variant :hs\n"), hs)
        for model, generated in (("h", h), ("hs", hs)):
            baseline = (ROOT / "cases" / "cliff" / f"cliff-urmi-long-mc-{model}.lisp").read_text(encoding="utf-8")
            # Verify every scientific Urmi-law parameter stays identical to
            # the actual reference cases, not merely to a duplicated fixture.
            import re
            for key in ("prepeak-points", "prepeak-cohesion-points", "peak-kappa",
                        "residual-kappa", "phi-peak-deg", "phi-post-rupture-deg",
                        "phi-residual-deg", "c-peak-pa", "c-post-rupture-pa",
                        "c-residual-pa", "beta", "postpeak-segments", "psi",
                        "youngs-modulus", "poisson-ratio", "density"):
                pattern = rf":{re.escape(key)}\s+([^\n]+)"
                reference_value = re.search(pattern, baseline)
                generated_value = re.search(pattern, generated)
                self.assertIsNotNone(reference_value, key)
                self.assertIsNotNone(generated_value, key)
                self.assertEqual(reference_value.group(1).strip(),
                                 generated_value.group(1).strip(), key)

    def test_crest_and_schema_bounds(self):
        with self.assertRaises(ValueError):
            make_plan(self.options(angles=[35]))
        with self.assertRaises(ValueError):
            make_plan(self.options(angles=[45], shelf_aspect=0.6))
        with self.assertRaises(ValueError):
            make_plan(self.options(angles=[45, 45]))
        with self.assertRaises(ValueError):
            make_plan(self.options(parallel=3))

    def test_generate_idempotently_without_overwriting(self):
        plan = make_plan(self.options())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prepare(plan, root)
            prepare(plan, root)
            cases = list(entries(plan, root))
            self.assertEqual(len(cases), 6)
            case = cases[0][2]
            case.write_text("other content", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare(plan, root)

    def test_completed_run_requires_manifest_frames_and_vtk(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            (run / "vtk").mkdir()
            (run / "manifest.json").write_text(json.dumps({"complete": True, "frames": 2}))
            with (run / "cliff-timeseries.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["frame", "time_s"])
                writer.writerows([[0, 0], [1, 0.1], [2, 0.2]])
            for i in range(3):
                (run / "vtk" / f"sim_{i:05d}.vtk").write_bytes(b"dummy")
            self.assertTrue(verified_run(run, 2))
            (run / "vtk" / "sim_00002.vtk").unlink()
            self.assertFalse(verified_run(run, 2))

    def test_renderer_uses_particle_geometry_not_graphs(self):
        def fake_reader(_):
            pts = np.array([[3.0, 4.0, 0.0], [5.0, 6.0, 0.0]])
            fields = {"size_x": np.array([0.5, 0.5]),
                      "size_y": np.array([0.5, 0.5]),
                      "mc-kappa": np.array([0.0, 0.5])}
            return pts, fields
        row = {"frame": "0", "time_s": "0.0", "max_disp_m": "0.0",
               "max_kappa": "0.5", "toe_runout_m": "0.0"}
        picture = draw_panel(fake_reader, Path("synthetic"), row, 934, 240, 42, 18, 55, "HS")
        self.assertEqual(picture.size, (934, 240))
        self.assertNotEqual(kappa_color(0.0), kappa_color(0.5))


if __name__ == "__main__":
    unittest.main()
