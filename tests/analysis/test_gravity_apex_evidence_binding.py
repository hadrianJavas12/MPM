"""Three NEW synthetic evidence-root controls; no earlier controls or native work.

Only the new binding helper is called on temporary JSON fixtures. An overall
failed Lisp reader gate can retain valid native short-output evidence; this
binding check does not certify those saved fields or declare a run PASS.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


class EvidenceBindingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix='mpm-evidence-helper-source-')
        original = ROOT / 'scripts/review-gravity-composite-apex.py'
        cls.source = Path(cls.source_temp.name) / original.name
        shutil.copyfile(original, cls.source)
        assert cls.source.read_bytes() == original.read_bytes()
        cls.source_hash = hashlib.sha256(cls.source.read_bytes()).hexdigest()
        spec = importlib.util.spec_from_file_location('gravity_evidence_binding_synthetic', cls.source)
        cls.reviewer = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.reviewer
        spec.loader.exec_module(cls.reviewer)

    @classmethod
    def tearDownClass(cls):
        try:
            assert hashlib.sha256(cls.source.read_bytes()).hexdigest() == cls.source_hash
        finally:
            cls.source_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mpm-binding-synthetic-only-')
        self.addCleanup(self.temp.cleanup)
        self.native = Path(self.temp.name) / 'native'
        self.run = self.native / 'observations'
        self.run.mkdir(parents=True)
        self.result = {
            'passed': False,
            'failure': ['saved-output', 'Synthetic later reader failure; not a native failure'],
            'passedGroups': ['strict-default', 'optional-input', 'short-output'],
            'physicalUpdatesExecuted': 2,
            'materialCallsAttempted': 1760,
            'materialCallsAccepted': 1760,
            'observations': {'observationsDirectory': str(self.run.resolve())},
        }
        write_json(self.native / 'result.json', self.result)

    def test_canonical_defaults_and_bounded_parent_binding(self):
        helper = self.reviewer.verify_evidence_root
        self.assertEqual(helper(self.run, None, False), self.run.resolve())
        self.assertEqual(helper(self.run, self.run, False), self.run.resolve())
        self.assertEqual(helper(self.run, self.native, True), self.native.resolve())
        # The binding is valid despite the retained later reader failure; a
        # separate independent native-field audit must still pass on its own.
        self.assertIs(self.result['passed'], False)

    def test_external_root_requires_bounded_flag_and_exact_observations_path(self):
        helper = self.reviewer.verify_evidence_root
        with self.assertRaises(ValueError):
            helper(self.run, self.native, False)
        for wrong_run, wrong_root in ((self.native / 'other-observations', self.native),
                                      (self.run, self.native / 'wrong-parent'),
                                      (self.run / 'nested', self.native)):
            with self.subTest(run=wrong_run, root=wrong_root):
                wrong_run.mkdir(parents=True, exist_ok=True)
                with self.assertRaises(ValueError):
                    helper(wrong_run, wrong_root, True)

    def test_short_output_update_call_counts_and_result_path_are_bound(self):
        changes = [
            ('passedGroups', ['strict-default', 'optional-input']),
            ('physicalUpdatesExecuted', 1),
            ('materialCallsAttempted', 1759),
            ('materialCallsAccepted', 1759),
            ('observations', {'observationsDirectory': str(self.native / 'other-observations')}),
        ]
        for key, value in changes:
            with self.subTest(key=key):
                result = deepcopy(self.result)
                result[key] = value
                write_json(self.native / 'result.json', result)
                with self.assertRaises(ValueError):
                    self.reviewer.verify_evidence_root(self.run, self.native, True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
