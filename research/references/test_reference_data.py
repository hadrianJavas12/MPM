"""Portable data integrity checks; no engine, PDF dependency or solver execution."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "research" / "references"
CONFIG_DIR = ROOT / "research" / "configs"
SOURCE_NAME = "Numerical Simulation Residual Soil TRX CU SIGMA ^0 FLAC_290825.pdf"
PLAN_NAME = "research/plans/MASTER_PLAN_CL_MPM_HARDENING_SOFTENING.md"
SOURCE_SHA256 = "acd60b668e3b6ed8c7a7378ae3afd053ca0419f4ed63aecc0031b019495f3979"
CONFIG_IDS = (
    "residual_soil_mc_h_reference",
    "residual_soil_mc_hs_reference",
    "zhan_cliff_h_reference",
    "zhan_cliff_hs_reference",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def value_records(node):
    """Walk source values and SI/config records without assuming a fixed layout."""
    if isinstance(node, dict):
        if "value" in node:
            yield node
        for child in node.values():
            yield from value_records(child)
    elif isinstance(node, list):
        for child in node:
            yield from value_records(child)


class ReferenceIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read_json(REFERENCE_DIR / "source_values.json")
        cls.configs = {name: read_json(CONFIG_DIR / (name + ".json")) for name in CONFIG_IDS}

    def test_source_identity_and_audit_scope(self):
        source = self.catalog["source_document"]
        self.assertEqual(source["filename"], SOURCE_NAME)
        self.assertEqual(source["sha256"], SOURCE_SHA256)
        self.assertEqual(source["page_count"], 28)
        self.assertEqual(source["visually_audited_pages"], [3, 6, 7, 11, 17])
        self.assertTrue(source["sha256_verified"])
        self.assertFalse(source["copied_into_repository"])

    def test_every_value_has_explicit_provenance(self):
        required = {"source_file", "page", "model_family", "units", "status", "notes", "origin"}
        for artifact in (self.catalog, *self.configs.values()):
            records = list(value_records(artifact))
            self.assertTrue(records)
            for record in records:
                with self.subTest(family=record.get("model_family"), value=record["value"]):
                    self.assertTrue(required.issubset(record))
                    self.assertEqual(record["status"], "reference_not_calibration")
                    self.assertTrue(record["units"])
                    self.assertTrue(record["notes"])
                    self.assertTrue(record["model_family"])
                    self.assertIn(record["source_file"], (SOURCE_NAME, PLAN_NAME))
                    if record["origin"] == "declared_assumption":
                        self.assertEqual(record["source_file"], PLAN_NAME)
                        self.assertIsNone(record["page"])
                    else:
                        self.assertIn(record["origin"], ("transcribed", "derived_SI"))
                        self.assertEqual(record["source_file"], SOURCE_NAME)
                        self.assertIn(record["page"], range(1, 29))

    def test_raw_columns_keep_blanks_and_distinct_strengths(self):
        data = self.catalog["datasets"]
        lab = data["residual_soil_laboratory_slide"]["values"]
        saniclay = data["residual_soil_saniclay_slide"]["values"]
        hs = data["residual_soil_mc_hs_slide"]["values"]
        peak = data["residual_soil_mc_peak_slide"]["values"]
        for column in (lab, saniclay, hs, peak):
            self.assertEqual(len(column), 21)
        self.assertIsNone(lab["young_modulus_effective"]["value"])
        self.assertIsNone(saniclay["cohesion_effective"]["value"])
        self.assertIsNone(hs["compression_index"]["value"])
        self.assertEqual(hs["cohesion_effective"]["value"], 0)
        self.assertEqual(peak["cohesion_effective"]["value"], 6.04)
        self.assertEqual(hs["young_modulus_effective"]["value"], 20000)

    def test_density_is_unit_weight_divided_by_declared_gravity(self):
        for name, expected_weight, expected_density in (
            ("residual_soil_mc_h_reference", 16830, 1716.1823864418532),
            ("zhan_cliff_h_reference", 18800, 1917.0664803985051),
        ):
            shared = self.configs[name]["shared"]
            self.assertEqual(shared["gravity"]["value"], 9.80665)
            self.assertEqual(shared["gravity"]["units"], "m/s^2")
            self.assertEqual(shared["unit_weight"]["value"], expected_weight)
            self.assertEqual(shared["unit_weight"]["units"], "N/m^3")
            self.assertEqual(shared["density"]["units"], "kg/m^3")
            self.assertAlmostEqual(shared["density"]["value"], expected_weight / 9.80665, places=10)
            self.assertAlmostEqual(shared["density"]["value"], expected_density, places=6)

    def test_residual_si_geometry_pressures_and_zero_strength_preserved(self):
        shared = self.configs["residual_soil_mc_h_reference"]["shared"]
        self.assertEqual(shared["geometry"]["type"]["value"], "3D_cylinder")
        self.assertEqual(shared["geometry"]["diameter"]["value"], 0.07)
        self.assertEqual(shared["geometry"]["height"]["value"], 0.14)
        self.assertEqual(shared["confining_pressures"]["value"], [100000, 200000])
        self.assertEqual(shared["confining_pressures"]["units"], "Pa")
        self.assertEqual(shared["young_modulus"]["value"], 20000000)
        self.assertEqual(shared["young_modulus"]["units"], "Pa")
        self.assertEqual(shared["cohesion"]["value"], 0)

    def test_residual_pair_has_identical_prepeak_and_declared_postpeak(self):
        hardening = self.configs["residual_soil_mc_h_reference"]
        softening = self.configs["residual_soil_mc_hs_reference"]
        self.assertEqual(hardening["shared"], softening["shared"])
        h_points = hardening["evolution"]["points"]
        hs_points = softening["evolution"]["points"]
        self.assertEqual(h_points, hs_points[:3])
        self.assertEqual([(p["kappa"]["value"], p["phi"]["value"]) for p in hs_points],
                         [(0, 0), (0.0068, 27.1), (0.037, 33.99), (0.1, 27.62), (0.2, 16.34)])
        self.assertEqual(h_points[-1]["phi"]["value"], 33.99)
        self.assertIn("plateau", hardening["evolution"]["postpeak"])
        self.assertIn("clamp", softening["evolution"]["postpeak"])
        self.assertEqual(hardening["evolution"]["peak_kappa"]["value"], 0.037)

    def test_zhan_pair_is_independent_and_does_not_invent_initial_strength(self):
        hardening = self.configs["zhan_cliff_h_reference"]
        softening = self.configs["zhan_cliff_hs_reference"]
        self.assertEqual(hardening["shared"], softening["shared"])
        self.assertEqual(hardening["evolution"]["points"], softening["evolution"]["points"][:1])
        self.assertEqual(hardening["evolution"]["prepeak"], softening["evolution"]["prepeak"])
        self.assertIn("unresolved", hardening["evolution"]["prepeak"])
        self.assertEqual(hardening["shared"]["material_family"], "zhan_clay_table_4_8_slide")
        self.assertNotEqual(hardening["shared"]["density"]["value"], 2000)
        self.assertEqual(hardening["shared"]["poisson_ratio"]["value"], 0.2)
        points = softening["evolution"]["points"]
        self.assertEqual([(p["kappa"]["value"], p["cohesion"]["value"], p["phi"]["value"]) for p in points],
                         [(0.05, 7000, 20), (0.2, 2000, 13)])
        self.assertEqual(hardening["shared"]["young_modulus_law"]["units"], "Pa")
        self.assertEqual(hardening["shared"]["young_modulus_law"]["value"],
                         "max(4000000, 25 * (p_effective_Pa + 100000))")

    def test_scaling_is_explicit_and_inactive(self):
        for config in self.configs.values():
            strain = config["shared"]["strain_coordinate"]
            self.assertEqual(strain["source_multiplier"]["value"], 1)
            self.assertEqual(strain["mapping_status"], "unverified_pending_M2")
        data = self.catalog["datasets"]
        self.assertEqual(data["residual_soil_mc_hs_friction"]["flac_strain_multiplier"]["value"], 20)
        zhan = data["zhan_clay_table_4_8_slide"]["values"]
        self.assertEqual(zhan["flac_shear_to_deviatoric_strain_ratio"]["value"], 0.5)
        self.assertEqual(zhan["water_bulk_modulus"]["units"], "unspecified_in_source")

    def test_every_configuration_remains_explicitly_non_executable(self):
        for name, config in self.configs.items():
            self.assertEqual(config["id"], name)
            self.assertEqual(config["kind"], "reference_case_proposal")
            self.assertEqual(config["status"], "reference_not_calibration")
            self.assertFalse(config["execution"]["enabled"])
            self.assertTrue(config["execution"]["blockers"])
            self.assertIn("not calibrated", config["scientific_scope"])


def write_evidence(result):
    files = [REFERENCE_DIR / "source_values.json", REFERENCE_DIR / "PROVENANCE.md",
             Path(__file__), *(CONFIG_DIR / (name + ".json") for name in CONFIG_IDS)]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "M1_reference_data_integrity",
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "command": "python research/references/test_reference_data.py --write-evidence",
        "python_version": sys.version.split()[0],
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "source_audit": read_json(REFERENCE_DIR / "source_values.json")["source_document"],
        "audit_scope": "Prior read-only PDF hash/text/render audit plus this run's JSON/stdlib integrity tests.",
        "file_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in files},
        "limits": ["No SBCL or solver execution.", "No constitutive verification or experimental validation.",
                   "Source strain mapping and zero-strength apex behavior pending M2.",
                   "Zhan-family initial hardening law unspecified by PDF; common prepeak path unresolved.",
                   "Source author attribution Zhan/Zang unresolved; original publication not audited."],
    }
    (REFERENCE_DIR / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_report = "--write-evidence" in sys.argv
    if write_report:
        sys.argv.remove("--write-evidence")
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceIntegrity))
    if write_report:
        write_evidence(result)
    raise SystemExit(0 if result.wasSuccessful() else 1)
