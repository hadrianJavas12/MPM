"""Analytical/input checks for the initializer; these do not run native CL-MPM."""

import importlib.util
import math
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location(
    "estimate_clay_parameters", Path(__file__).with_name("estimate-clay-parameters.py")
)
ESTIMATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ESTIMATOR)


class InitializerTests(unittest.TestCase):
    def write_curve(self, directory, text):
        path = Path(directory) / "curve.csv"
        path.write_text(text, encoding="utf-8")
        return path

    def test_known_elastic_slope_intercept_and_strength_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_curve(
                directory,
                "axial_strain_pct,deviatoric_stress_kpa\n"
                "0,3\n0.1,8\n0.2,13\n0.3,18\n0.4,23\n5,49\n7,50\n10,51\n",
            )
            result = ESTIMATOR.estimate(path, source_kind="synthetic")
            self.assertAlmostEqual(result["parameters"]["youngsModulusPa"], 5_000_000)
            self.assertAlmostEqual(result["parameters"]["undrainedStrengthPa"], 25_000)
            self.assertAlmostEqual(result["parameters"]["nativeVmRhoPa"], math.sqrt(8 / 3) * 25_000)
            self.assertAlmostEqual(result["elastic_regression"]["intercept_kpa"], 3)
            self.assertAlmostEqual(result["elastic_regression"]["r_squared"], 1)
            self.assertFalse(result["scientific_validation"])
            self.assertFalse(result["native_forward_optimization"])
            self.assertFalse(result["late_strength"]["plateau_verified"])

    def test_rejects_missing_units_nonfinite_and_unloading(self):
        cases = [
            ("strain,stress\n0,0\n", "unit-bearing headers"),
            ("axial_strain_pct,deviatoric_stress_kpa\n0,nan\n", "non-finite"),
            ("axial_strain_pct,deviatoric_stress_kpa\n0,0\n0.2,10\n0.1,5\n", "strain decreases"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for content, expected in cases:
                with self.subTest(expected=expected):
                    path = self.write_curve(directory, content)
                    with self.assertRaisesRegex(ValueError, expected):
                        ESTIMATOR.estimate(path)

    def test_selects_measured_strain_column_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_curve(
                directory,
                "axial_strain_pct,particle_extents_axial_strain_pct,deviatoric_stress_kpa\n"
                "0,0,0\n0.2,0.1,5\n0.4,0.2,10\n0.6,0.3,15\n0.8,0.4,20\n"
                "5.1,5,50\n7.1,7,50\n10.1,10,50\n",
            )
            original = path.read_bytes()
            result = ESTIMATOR.estimate(
                path, source_kind="synthetic",
                strain_column="particle_extents_axial_strain_pct",
            )
            self.assertAlmostEqual(result["parameters"]["youngsModulusPa"], 5_000_000)
            self.assertEqual(result["source"]["strain_column"], "particle_extents_axial_strain_pct")
            self.assertEqual(result["elastic_regression"]["point_count"], 5)
            self.assertEqual(path.read_bytes(), original)

    def test_rejects_insufficient_windows_and_negative_elastic_slope(self):
        cases = [
            ("0,0\n0.2,10\n5,50\n7,50\n10,50\n", "elastic window"),
            ("0,0\n0.2,10\n0.4,20\n5,50\n7,50\n", "late-strength window"),
            ("0,20\n0.2,10\n0.4,0\n5,50\n7,50\n10,50\n", "slope must be positive"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for data, expected in cases:
                with self.subTest(expected=expected):
                    path = self.write_curve(directory, "axial_strain_pct,deviatoric_stress_kpa\n" + data)
                    with self.assertRaisesRegex(ValueError, expected):
                        ESTIMATOR.estimate(path)


if __name__ == "__main__":
    unittest.main()
