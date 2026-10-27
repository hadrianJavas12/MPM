"""Focused synthetic helpers only; these controls do not run MPM or audit a slope."""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("urmi_saved_review", ROOT / "scripts/review-urmi-damage40.py")
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)
CONTRACT = json.loads((ROOT / "research/references/urmi-mc-damage40/contract.json").read_text(encoding="utf-8"))


class UrmiSavedReviewControls(unittest.TestCase):
    def test_streaming_frame_boundaries_ids_and_fortran_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "particles.csv"
            path.write_text("frame,particle_id,x\n0,0,1D-2\n0,1,2d-2\n1,0,3e-2\n1,1,4e-2\n", encoding="utf-8")
            stream = review.csv_frames(path)
            first, values = next(stream)
            self.assertEqual(first, 0)
            np.testing.assert_array_equal(values["particle_id"], [0, 1])
            np.testing.assert_allclose(values["x"], [0.01, 0.02])
            self.assertEqual(next(stream)[0], 1)
            self.assertRaises(StopIteration, next, stream)

    def test_stream_rejects_reordered_nonfinite_and_truncated_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "particles.csv"
            for text in ("frame,x\n1,2\n0,3\n", "frame,x\n0,nan\n", "frame,x\n0,\n", "frame,x,x\n0,1,2\n"):
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    list(review.csv_frames(path))

    def test_independent_table_endpoints_origin_and_strength_damage(self):
        nodes, bound = review.reference_table(CONTRACT["material"])
        self.assertEqual(len(nodes) - 1, 26)
        self.assertLessEqual(bound, 101.25)
        self.assertEqual(nodes[0, 2], 40500)
        self.assertEqual(nodes[-1, 2], 1000)
        self.assertTrue((np.diff(nodes[:, 1]) > 0).all())
        self.assertTrue((np.diff(nodes[:, 2]) <= 0).all())
        origin = 0.02
        actual = review.law_strength(nodes[:, 1] + origin, np.full(len(nodes), origin), nodes)
        np.testing.assert_allclose(actual, nodes[:, 2], atol=1e-10, rtol=1e-11)
        self.assertAlmostEqual(1 - actual[-1] / 40500, 0.9753086419753086)
        # A nonzero history origin keeps peak strength before activation.
        self.assertEqual(review.law_strength(np.array([0.01]), np.array([origin]), nodes)[0], 40500)

    def test_six_plane_current_J_and_tresca_not_von_mises(self):
        values = {k: np.zeros(2) for k in review.STRESS_COLUMNS}
        values.update(J=np.array([0.8, 1.7]), cohesion_pa=np.full(2, 40500), friction_rad=np.zeros(2))
        values["sig_xx_pa"] = np.full(2, 40500)
        values["sig_yy_pa"] = np.full(2, -40500)
        np.testing.assert_allclose(review.six_plane_residual(values), [0, 0], atol=1e-10)
        values["sig_xx_pa"] += 100
        np.testing.assert_allclose(review.six_plane_residual(values), values["J"] * 100, atol=1e-10)

    def test_physical_graph_cohort_and_component_mass_tie(self):
        points = np.array([[0, 0], [3, 7], [3.5, 7], [10, 7], [10.5, 7]], dtype=float)
        cohort = (points[:, 0] > 2) & (points[:, 1] > 6)
        graph = review.graph_for(points, cohort, 1.01)
        self.assertNotIn(0, graph)
        masses = np.array([20, 1, 1, 1, 1], dtype=float)
        selected = review.largest_component(cohort, graph, masses)
        np.testing.assert_array_equal(selected, [1, 2])
        masses[3] = 2
        np.testing.assert_array_equal(review.largest_component(cohort, graph, masses), [3, 4])

    def test_persistence_requires_all_actual_states_and_full_second(self):
        observer = CONTRACT["observer"]
        time = np.arange(0, 1.01, 0.2)
        self.assertEqual(review.sustained_interval(time, np.full(6, 0.002), observer)["status"], "PASS")
        bad = np.full(6, 0.002)
        bad[3] = 0.001
        self.assertNotEqual(review.sustained_interval(time, bad, observer)["status"], "PASS")
        self.assertEqual(review.sustained_interval(time[:5], bad[:5], observer)["status"], "NOT_EVALUATED")

    def test_preparation_zero_force_norm_is_ineligible_and_hold_not_faked(self):
        columns = ["updates", "native_time_s", "force_defined", "RF", "free_force_numerator2",
                   "free_force_denominator2", "free_KE", "free_nodal_mass", "RK", "prior_consecutive", "prior_hold", "damping"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preparation.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                for index in range(200):
                    writer.writerow([index + 1, 2 + index * 0.02, 1, 1e-6, 1e-12, 1, 0, 1, 0, 50, index, 0 if index >= 100 else 1])
            self.assertEqual(review.preparation_check(path, CONTRACT, True)["status"], "PASS")
            # An early failed check may legitimately recover. Invalidate the
            # LAST damped check so no qualifying window precedes the hold.
            rows = list(csv.reader(path.read_text().splitlines()))
            rows[100][2:6] = ["0", "0", "0", "0"]
            with path.open("w", newline="") as stream:
                csv.writer(stream).writerows(rows)
            with self.assertRaises(ValueError):
                review.preparation_check(path, CONTRACT, True)

    def test_preparation_counts_without_physical_duration_are_rejected(self):
        columns = ["updates", "native_time_s", "force_defined", "RF", "free_force_numerator2",
                   "free_force_denominator2", "free_KE", "free_nodal_mass", "RK", "prior_consecutive", "prior_hold", "damping"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "preparation.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(columns)
                for index in range(150):
                    writer.writerow([index + 1, 2 + index * 1e-5, 1, 1e-6, 1e-12, 1, 0, 1, 0, 50, index, 0 if index >= 50 else 1])
            with self.assertRaises(ValueError):
                review.preparation_check(path, CONTRACT, True)

    def test_contract_keeps_damage_and_scientific_flags_separate(self):
        self.assertEqual(CONTRACT["media"]["field"], "mc-strength-damage")
        self.assertEqual(CONTRACT["media"]["colourMaximum"], 1)
        self.assertFalse(CONTRACT["verdict"]["automaticScientificValidation"])
        self.assertFalse(CONTRACT["verdict"]["automaticLandslideVerification"])
        self.assertEqual(CONTRACT["configuration"]["duration"], 60)
        self.assertEqual(CONTRACT["observer"]["cohortInitialYGreaterM"], 6)


if __name__ == "__main__":
    unittest.main()
