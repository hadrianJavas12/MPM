"""Synthetic controls for a fixed physical observer across coarse/fine grids.

No saved-run files, native material, MPM, renderer or replay are executed.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def import_source(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_states(initial, masses, times=(0., .5, 1., 2., 3.), displacement=(.6, -.3),
                velocity=(.6, -.3), moving=None, stop_displacement_at=1.):
    initial, masses = np.asarray(initial, dtype=float), np.asarray(masses, dtype=float)
    moving = np.ones(len(masses), dtype=bool) if moving is None else np.asarray(moving, dtype=bool)
    states = []
    for frame, time in enumerate(times):
        positions = initial.copy()
        positions[moving] += min(time, stop_displacement_at) * np.asarray(displacement)
        speeds = np.zeros_like(initial)
        speeds[moving] = velocity
        states.append({"frame": frame, "time": time, "positions": positions,
                       "velocity": speeds, "kappa": np.zeros(len(masses)),
                       "J": np.ones(len(masses)), "masses": masses.copy(),
                       "kinetic": float(.5 * np.sum(masses[:, None] * speeds * speeds))})
    return states


class PhysicalObserverControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wrapper = import_source("refinement_observer_under_test", ROOT / "scripts/review-gravity-refinement.py")
        cls.support = tempfile.TemporaryDirectory(prefix="mpm-observer-synthetic-")
        support = Path(cls.support.name)
        for name in ("review-gravity-slope.py", "plot_m5_cliff_comparison.py"):
            shutil.copyfile(ROOT / "scripts" / name, support / name)
        cls.native = cls.wrapper.load_review_module(support)
        cls.contract = json.loads((ROOT / "research/references/unnotched-mc-ssr/refinement-contract.json").read_text(encoding="utf-8-sig"))
        cls.observer = cls.wrapper.validate_observer(copy.deepcopy(cls.contract))
        cls.beta = float(np.arctan(.5))

    @classmethod
    def tearDownClass(cls):
        cls.support.cleanup()

    def observe(self, initial, masses, **kwargs):
        states = make_states(initial, masses, **kwargs)
        return self.wrapper.common_physical_windows(self.native, states, np.asarray(initial, dtype=float),
                                                     np.asarray(masses, dtype=float), self.beta, self.observer)

    def test_physically_equivalent_coarse_and_fine_mass(self):
        coarse = np.array([(x, y) for x in (3.25, 3.75) for y in (3.25, 3.75)])
        fine = np.array([(x, y) for x in (3.125, 3.375, 3.625, 3.875) for y in (3.125, 3.375, 3.625, 3.875)])
        first, second = self.observe(coarse, np.ones(4)), self.observe(fine, np.full(16, .25))
        self.assertEqual((first["cohortCount"], second["cohortCount"]), (4, 16))
        self.assertEqual(first["cohortMassKgPerM"], second["cohortMassKgPerM"])
        for result in (first, second):
            self.assertEqual(result["windows"]["entire"]["status"], "PASS")
            self.assertEqual(result["windows"]["entire"]["candidate"]["componentMassFraction"], 1.)

    def test_h_scaled_apparent_pass_does_not_relax_physical_motion(self):
        initial = np.array([[3., 3.], [3.25, 3.], [3.5, 3.]])
        masses = np.ones(3)
        states = make_states(initial, masses, displacement=(.2, -.2), velocity=(.2, -.2))
        selected = np.ones(3, dtype=bool)
        graph = self.native.initial_graph(initial, selected, .5)
        old = self.native.motion_window(states, 0, graph, selected, masses, .5, self.beta, "native-fine-h")
        self.assertEqual(old["status"], "PASS")
        new = self.wrapper.common_physical_windows(self.native, states, initial, masses, self.beta, self.observer)
        self.assertEqual(new["windows"]["entire"]["status"], "NOT_DETECTED")

    def test_common_cohort_excludes_fine_native_support_band(self):
        initial = [[1.5, 3.], [3., 1.5], [2., 3.], [3., 3.], [3.5, 3.]]
        result = self.observe(initial, [100., 100., 100., 1., 1.])
        self.assertEqual(result["cohortCount"], 2)
        self.assertEqual(result["cohortMassKgPerM"], 2.)

    def test_physical_graph_radius_not_native_fine_radius(self):
        masses, moving = np.array([1., 1., 18.]), [True, True, False]
        initial = np.array([[3., 3.], [3.75, 3.], [7., 3.]])
        states = make_states(initial, masses, moving=moving)
        common = self.wrapper.common_physical_windows(self.native, states, initial, masses, self.beta, self.observer)
        self.assertEqual(common["windows"]["entire"]["status"], "PASS")
        self.assertAlmostEqual(common["windows"]["entire"]["candidate"]["componentMassFraction"], .1)
        native_graph = self.native.initial_graph(initial, np.ones(3, dtype=bool), .5)
        old = self.native.motion_window(states, 0, native_graph, np.ones(3, dtype=bool), masses, .5, self.beta, "fine")
        self.assertEqual(old["status"], "NOT_DETECTED")
        initial[1, 0] = 4.02
        apart = self.observe(initial, masses, moving=moving)
        self.assertEqual(apart["windows"]["entire"]["status"], "NOT_DETECTED")

    def test_post2s_window_discards_earlier_displacement(self):
        result = self.observe([[3., 3.], [3.5, 3.]], [1., 1.])
        self.assertEqual(result["windows"]["entire"]["status"], "PASS")
        self.assertEqual(result["windows"]["post2s"]["status"], "NOT_DETECTED")
        self.assertEqual(result["windows"]["post2s"]["referenceTimeS"], 2.)

    def test_short_window_cannot_prove_persistence(self):
        result = self.observe([[3., 3.], [3.5, 3.]], [1., 1.], times=(0., .4, .9))
        self.assertEqual(result["windows"]["entire"]["status"], "NOT_EVALUATED")

    def test_velocity_threshold_is_strict(self):
        initial, masses = [[3., 3.], [3.5, 3.]], [1., 1.]
        at = self.observe(initial, masses, velocity=(.001, 0.))
        above = self.observe(initial, masses, velocity=(.0010000001, 0.))
        self.assertEqual(at["windows"]["entire"]["status"], "NOT_DETECTED")
        self.assertEqual(above["windows"]["entire"]["status"], "PASS")

    def test_physical_toe_threshold_is_strict(self):
        masses = np.ones(2)
        states = make_states([[32.5, 3.], [32.5, 4.]], masses, times=(0., 1.), displacement=(0., 0.))
        states[1]["positions"][0, 0] = np.nextafter(32.5, np.inf)
        result = self.wrapper.physical_runout(states, masses, self.observer)
        self.assertEqual(result[0]["massFractionPastPhysicalToe"], 0.)
        self.assertEqual(result[1]["massFractionPastPhysicalToe"], .5)

    def test_contract_drift_rejected_and_inputs_unchanged(self):
        for key, value in (("initialAdjacencyRadiusM", .505), ("movingMinimumDxM", .125),
                           ("movingMinimumDownslopeDisplacementM", .25), ("runoutXGreaterThanM", 32.25)):
            changed = copy.deepcopy(self.contract)
            changed["comparisonObserver"][key] = value
            with self.assertRaises(ValueError):
                self.wrapper.validate_observer(changed)
        initial, masses = np.array([[3., 3.], [3.5, 3.]]), np.array([1., 1.])
        states = make_states(initial, masses)
        before, before_observer = copy.deepcopy(states), copy.deepcopy(self.observer)
        self.wrapper.common_physical_windows(self.native, states, initial, masses, self.beta, self.observer)
        self.wrapper.physical_runout(states, masses, self.observer)
        for old, new in zip(before, states):
            for key in old:
                if isinstance(old[key], np.ndarray):
                    np.testing.assert_array_equal(old[key], new[key])
                else:
                    self.assertEqual(old[key], new[key])
        np.testing.assert_array_equal(initial, [[3., 3.], [3.5, 3.]])
        np.testing.assert_array_equal(masses, [1., 1.])
        self.assertEqual(before_observer, self.observer)


if __name__ == "__main__":
    unittest.main()
