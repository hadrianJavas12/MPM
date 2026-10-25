"""Synthetic metadata/field controls only; no native run, saved-run audit or render.

The reviewer and its companion sources are copied before import. Numeric
fixtures exercise verify_variant only; the unchanged base auditor is replaced
by a small explicit fixture reader, so these are not whole-run integrity tests.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path('research/references/unnotched-mc-ssr/composite-apex-srf1p6-contract.json')
STRESS = [f'sig_{axis}_pa' for axis in ('xx', 'yy', 'zz', 'yz', 'xz', 'xy')]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FixtureReader:
    STATE_ATOL = 1e-11
    STRESS_COLUMNS = STRESS

    def __init__(self, particles, fields):
        self.particles, self.fields = particles, fields

    @staticmethod
    def close(actual, expected):
        return bool(np.allclose(actual, expected, atol=1e-11, rtol=1e-11))

    @staticmethod
    def integral(values, label):
        if not np.equal(values, np.rint(values)).all():
            raise ValueError(label)
        return values.astype(int)

    def native_csv(self, path):
        return self.particles

    @staticmethod
    def stress_constants(run, source):
        return {'stress-atol': 1e-6, 'stress-rtol': 1e-11}, []

    def read_cliff_vtk(self, path):
        frame = int(path.stem.rsplit('_', 1)[1])
        return None, self.fields[frame]


class SyntheticRun:
    def __init__(self, directory, reviewer, contract, bounded=False):
        self.run, self.reviewer, self.contract = directory, reviewer, deepcopy(contract)
        m, g, n, gravity = (contract[key] for key in ('referenceMaterial', 'geometry', 'numerics', 'gravity'))
        config = dict(E=m['youngsModulusPa'], nu=m['poissonRatio'],
            referenceCohesionPa=m['cohesionCauchyPa'], referenceFrictionDeg=m['frictionDeg'],
            density=m['unitWeightNPerM3'] / abs(gravity['fullAccelerationMPerS2']),
            domainWidth=g['domainWidthM'], domainHeight=g['domainHeightM'], height=g['heightM'],
            crestLength=g['rearCrestM'], width=g['rearCrestM'] + g['faceHorizontalM'],
            baseHeight=g['foundationDepthM'], slope=math.degrees(math.atan2(g['heightM'], g['faceHorizontalM'])),
            meshSize=n['meshSizeM'], mpsPerCell=n['particlesPerAxisPerCell'], workers=n['workers'],
            timeStepScale=n['timeStepScale'], duration=n['durationS'], frames=n['frames'],
            maxUpdates=n['maxUpdates'], damping=n['damping'], gravity=gravity['fullAccelerationMPerS2'],
            gravityRampDuration=gravity['rampDurationS'], strengthReductionFactor=contract['independentTrials'][0],
            materialVariant=reviewer.VARIANT, materialClass=reviewer.PARTICLE_CLASS)
        config.update(contract['variantMetadata'])
        if bounded:
            config.update(duration=2e-5, gravityRampDuration=1e-5, frames=3, maxUpdates=2)
        self.manifest = dict(config=config, materialVariant=reviewer.VARIANT,
            materialClass=reviewer.PARTICLE_CLASS, notchCount=0, driverCount=0, massScale=1, damping=0,
            updates=2 if bounded else 6000, savedFrames=config['frames'])
        self.manifest.update(contract['variantMetadata'])
        count = config['frames']
        self.states = [{'frame': frame, 'time': config['duration'] * frame / (count - 1)} for frame in range(count)]
        frames = np.repeat(np.arange(count), 2)
        j = np.tile([.8, 1.2], count)
        c = m['cohesionCauchyPa'] / config['strengthReductionFactor']
        phi = math.atan(math.tan(math.radians(m['frictionDeg'])) / config['strengthReductionFactor'])
        self.particles = dict(frame=frames, J=j, cohesion_pa=np.full(len(frames), c),
            friction_rad=np.full(len(frames), phi), plastic_volume=np.zeros(len(frames)),
            plastic_work_pa=np.zeros(len(frames)))
        for i in range(3):
            for k in range(3):
                self.particles[f'F_{i}{k}'] = j.copy() if i == k == 0 else np.full(len(frames), float(i == k))
        for name in STRESS:
            self.particles[name] = np.zeros(len(frames))
        final = frames == count - 1
        self.particles['plastic_volume'][final] = [5e-4, 3e-4]
        self.particles['plastic_work_pa'][final] = [2, 1]
        for name in STRESS[:3]:
            self.particles[name][final] = c / math.tan(phi)
        self.fields = {}
        for frame in range(count):
            rows = frames == frame
            self.fields[frame] = {
                'mc-apex-active-last': np.array([1., 0.]) if frame == count - 1 else np.zeros(2),
                'mc-apex-lambda-last': np.array([2e-5, 0.]) if frame == count - 1 else np.zeros(2),
                'mc-plastic-volume': self.particles['plastic_volume'][rows].copy(),
                'mc-plastic-work-j-m3': self.particles['plastic_work_pa'][rows].copy()}
        self.base = FixtureReader(self.particles, self.fields)
        self.bounded = bounded

    def review(self, bounded=None):
        write_json(self.run / 'manifest.json', self.manifest)
        return self.reviewer.verify_variant(self.base, self.run, self.contract, self.states,
            self.bounded if bounded is None else bounded)

    @property
    def last(self):
        return len(self.states) - 1


class CompositeApexReviewControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.support = tempfile.TemporaryDirectory(prefix='mpm-apex-analysis-source-')
        source = Path(cls.support.name)
        cls.source_hashes = {}
        for relative in (Path('scripts/review-gravity-composite-apex.py'),
                         Path('scripts/review-gravity-slope.py'), Path('scripts/plot_m5_cliff_comparison.py'), CONTRACT):
            original, target = ROOT / relative, source / relative.name
            shutil.copyfile(original, target)
            assert original.read_bytes() == target.read_bytes()
            cls.source_hashes[target] = sha(target)
        spec = importlib.util.spec_from_file_location('composite_apex_review_synthetic', source / 'review-gravity-composite-apex.py')
        cls.reviewer = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.reviewer
        spec.loader.exec_module(cls.reviewer)
        cls.contract = json.loads((source / CONTRACT.name).read_text(encoding='utf-8-sig'))

    @classmethod
    def tearDownClass(cls):
        try:
            for path, expected in cls.source_hashes.items():
                assert sha(path) == expected, 'Copied analysis source changed during synthetic controls'
        finally:
            cls.support.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mpm-apex-synthetic-only-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def fixture(self, bounded=False):
        return SyntheticRun(self.directory, self.reviewer, self.contract, bounded)

    def native_proof(self):
        records, actions = [], []
        for relative in self.reviewer.REQUIRED + ['libs/kirchoff.dll']:
            path = self.directory / 'source' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'SYNTHETIC FORMAT FIXTURE ONLY; never loaded or executed\n')
            records.append(dict(path='source/' + relative, bytes=path.stat().st_size, sha256=sha(path)))
            if relative in self.reviewer.REQUIRED:
                actions.append(dict(source=str(path.resolve()), firstParty=True, operation='load-op', event='performing'))
        manifest = {'files': records}
        backend = dict(modulePath=str((self.directory / 'source/libs/kirchoff.dll').resolve()),
            sha256=sha(self.directory / 'source/libs/kirchoff.dll'),
            verifiedBy='GetModuleHandleW/GetModuleFileNameW', nativeMcEntryPresent=True)
        provenance = dict(sourceSnapshotExactLoadedBytes=True, copiedByteEqualityBeforeLoad=True,
            copiedFiles=[row['path'] for row in records], verifiedAsdfActions=actions, nativeBackend=backend)
        write_json(self.directory / 'source/source-manifest.json', manifest)
        write_json(self.directory / 'source-provenance.json', provenance)
        return manifest, provenance

    def test_expected_native_source_and_runtime_schema(self):
        self.native_proof()
        result = self.reviewer.verify_native_sources(self.directory)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['frozenSourcesVerified'], len(self.reviewer.REQUIRED) + 1)

    def test_reject_duplicate_manifest_and_changed_source(self):
        manifest, _ = self.native_proof()
        manifest['files'].append(deepcopy(manifest['files'][0]))
        write_json(self.directory / 'source/source-manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.reviewer.verify_native_sources(self.directory)
        self.native_proof()
        (self.directory / 'source' / self.reviewer.REQUIRED[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            self.reviewer.verify_native_sources(self.directory)

    def test_reject_unloaded_optional_and_wrong_mapped_dll(self):
        _, provenance = self.native_proof()
        provenance['verifiedAsdfActions'].pop()
        write_json(self.directory / 'source-provenance.json', provenance)
        with self.assertRaisesRegex(ValueError, 'not recorded loaded'):
            self.reviewer.verify_native_sources(self.directory)
        _, provenance = self.native_proof()
        provenance['nativeBackend']['modulePath'] = str(self.directory / 'other.dll')
        write_json(self.directory / 'source-provenance.json', provenance)
        with self.assertRaisesRegex(ValueError, 'mapped DLL path'):
            self.reviewer.verify_native_sources(self.directory)

    def test_exact_variant_class_and_convention_metadata(self):
        for target, key, value in (('manifest', 'materialVariant', 'strict'),
                                   ('config', 'materialClass', 'UNKNOWN:CLASS'),
                                   ('manifest', 'apexConvention', 'a different flow'),
                                   ('config', 'apexCapBandPolicy', 'fallback after rejection')):
            with self.subTest(target=target, key=key):
                f = self.fixture()
                (f.manifest if target == 'manifest' else f.manifest['config'])[key] = value
                with self.assertRaises(ValueError):
                    f.review()

    def test_full_input_contract_slope_and_integer_guards(self):
        for key, value in (('slope', 30.), ('gravity', -10.), ('timeStepScale', .3),
                           ('workers', 1.), ('frames', 61.), ('maxUpdates', 60000.)):
            with self.subTest(key=key):
                f = self.fixture()
                f.manifest['config'][key] = value
                with self.assertRaises(ValueError):
                    f.review()

    def test_bounded_overrides_require_explicit_flag_and_exact_scope(self):
        f = self.fixture(bounded=True)
        self.assertEqual(f.review()['status'], 'PASS')
        with self.assertRaises(ValueError):
            f.review(bounded=False)
        for key, value in (('updates', 1), ('savedFrames', 2)):
            f = self.fixture(bounded=True)
            f.manifest[key] = value
            with self.assertRaisesRegex(ValueError, 'two updates'):
                f.review()
        f = self.fixture(bounded=True)
        f.manifest['config']['meshSize'] = .5
        with self.assertRaises(ValueError):
            f.review()

    def test_invalid_flag_q_and_nonfinite_fields_reject(self):
        for flag, q in ((.5, 2e-5), (1., 0.), (0., 2e-5), (1., -2e-5), (1., np.nan)):
            with self.subTest(flag=flag, q=q):
                f = self.fixture()
                f.fields[f.last]['mc-apex-active-last'][0] = flag
                f.fields[f.last]['mc-apex-lambda-last'][0] = q
                with self.assertRaises(ValueError):
                    f.review()

    def test_wrong_hydrostatic_cap_and_double_J_reject(self):
        for double_j in (False, True):
            with self.subTest(double_j=double_j):
                f = self.fixture()
                index = 2 * f.last
                if double_j:
                    for name in STRESS[:3]:
                        f.particles[name][index] *= f.particles['J'][index]
                else:
                    f.particles[STRESS[0]][index] += 1.
                with self.assertRaisesRegex(ValueError, 'hydrostatic cap'):
                    f.review()

    def test_csv_vtk_volume_and_work_mismatches_reject(self):
        for name in ('mc-plastic-volume', 'mc-plastic-work-j-m3'):
            with self.subTest(name=name):
                f = self.fixture()
                f.fields[f.last][name][0] += .01
                with self.assertRaisesRegex(ValueError, 'CSV/VTK'):
                    f.review()

    def test_negative_and_decreasing_cumulative_volume_reject(self):
        for negative in (True, False):
            with self.subTest(negative=negative):
                f = self.fixture()
                frame, value = (f.last, -.01) if negative else (f.last - 1, .01)
                f.particles['plastic_volume'][2 * frame] = value
                f.fields[frame]['mc-plastic-volume'][0] = value
                with self.assertRaisesRegex(ValueError, 'plastic volume'):
                    f.review()

    def test_last_q_is_not_a_sparse_history_delta_or_ever_active_flag(self):
        f = self.fixture()
        result = f.review()
        self.assertEqual(result['status'], 'PASS')
        final = result['frames'][-1]
        self.assertEqual(final['activeLastReturnCount'], 1)
        self.assertNotEqual(final['maximumLastMultiplier'], final['maximumCumulativePlasticVolume'])
        self.assertGreater(f.particles['plastic_volume'][-1], 0.)
        self.assertEqual(f.fields[f.last]['mc-apex-active-last'][-1], 0.)
        self.assertEqual(f.fields[f.last]['mc-apex-lambda-last'][-1], 0.)


if __name__ == '__main__':
    unittest.main(verbosity=2)
