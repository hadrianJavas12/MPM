"""New CSV-wrapper glue controls only; no old observer controls or actual runs."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("composite_csv_glue", ROOT / "scripts/review-gravity-composite-refinement.py")
WRAPPER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = WRAPPER
SPEC.loader.exec_module(WRAPPER)


class CompletedReviewBindingControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mpm-csv-binding-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name).resolve()
        self.contract = self.run / "audit-contract.json"
        self.contract.write_text("{}\n", encoding="utf-8")
        self.sha = hashlib.sha256(self.contract.read_bytes()).hexdigest()
        for name, text in (("manifest.json", '{"complete":true}'), ("history.csv", "synthetic history"),
                           ("particles.csv", "synthetic particles")):
            (self.run / name).write_text(text, encoding="utf-8")
        inputs = [{"path": str(path), "bytes": path.stat().st_size,
                   "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                  for path in (self.run / name for name in ("manifest.json", "history.csv", "particles.csv"))]
        self.report = {"integrityStatus": "PASS", "nativeComplete": True, "boundedControlOnly": False,
            "analysisSourceAfterMatch": True, "sourceVerification": {"status": "PASS"},
            "nativeEvidenceRoot": str(self.run), "variantReview": {"status": "PASS",
                "materialVariant": WRAPPER.VARIANT, "boundedControlOnly": False},
            "baseReview": {"integrityStatus": "PASS", "nativeComplete": True, "runDirectory": str(self.run),
                "contract": {"path": str(self.contract), "sha256": self.sha}, "inputHashes": inputs}}

    def bind(self, report=None, run=None, sha=None):
        return WRAPPER.bind_review(run or self.run, report or self.report, sha or self.sha)

    def test_matching_review_is_bound_without_mutation(self):
        before = copy.deepcopy(self.report)
        self.assertEqual(self.bind(), self.report["baseReview"])
        self.assertEqual(self.report, before)

    def test_swapped_run_and_duplicate_input_records_rejected(self):
        with self.assertRaises(ValueError):
            self.bind(run=self.run / "another-run")
        changed = copy.deepcopy(self.report)
        changed["baseReview"]["inputHashes"].append(changed["baseReview"]["inputHashes"][0])
        with self.assertRaises(ValueError):
            self.bind(report=changed)

    def test_changed_saved_csv_and_contract_bytes_rejected(self):
        (self.run / "particles.csv").write_text("changed particles", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.bind()
        # Isolate the second rejection: a stale CSV must not mask a missing
        # contract-byte check.
        (self.run / "particles.csv").write_text("synthetic particles", encoding="utf-8")
        self.contract.write_text('{"changed":true}', encoding="utf-8")
        with self.assertRaises(ValueError):
            self.bind()

    def test_bounded_incomplete_and_failed_proof_rejected(self):
        for key, value in (("boundedControlOnly", True), ("nativeComplete", False),
                           ("analysisSourceAfterMatch", False), ("mediaError", "retained failure")):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.report)
                changed[key] = value
                with self.assertRaises(ValueError):
                    self.bind(report=changed)
        changed = copy.deepcopy(self.report)
        changed["sourceVerification"]["status"] = "FAIL"
        with self.assertRaises(ValueError):
            self.bind(report=changed)


class PairGlueControls(unittest.TestCase):
    def test_only_registered_mesh_change_is_accepted(self):
        coarse = {"meshSize": 1., "materialVariant": WRAPPER.VARIANT, "strengthReductionFactor": 1.6}
        fine = {**coarse, "meshSize": .5}
        contract = {"onlyAssignedDifference": {"meshSizeM": [1, .5]}}
        self.assertEqual(WRAPPER.check_pair_configs(coarse, fine, contract),
                         [{"key": "meshSize", "coarse": 1., "fine": .5}])
        for changed in ({**fine, "extra": 0}, {**fine, "strengthReductionFactor": 2.},
                        {**fine, "materialVariant": "strict"}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                WRAPPER.check_pair_configs(coarse, changed, contract)

    def test_apex_last_q_is_copied_not_inferred_from_volume(self):
        frames = [{"frame": 0, "timeS": 0., "maximumLastMultiplier": 0., "maximumCumulativePlasticVolume": 0.},
                  {"frame": 1, "timeS": .1, "maximumLastMultiplier": .01, "maximumCumulativePlasticVolume": .125}]
        report = {"variantReview": {"frames": frames}}
        before = copy.deepcopy(report)
        states = [{"frame": row["frame"], "time": row["timeS"]} for row in frames]
        native = SimpleNamespace(TIME_ATOL=1e-10, TIME_RTOL=1e-10)
        result = WRAPPER.apex_summary(report, states, native)
        self.assertEqual(result["frames"][1]["maximumLastMultiplier"], .01)
        self.assertTrue(result["lastMultiplierIsNotCumulativeVolumeDifference"])
        self.assertEqual(report, before)
        states[1]["time"] = .2
        with self.assertRaises(ValueError):
            WRAPPER.apex_summary(report, states, native)


if __name__ == "__main__":
    unittest.main(verbosity=2)
