"""One saved-only terminal interpretation; no solver/review/render rerun.

Retains the original reviewer unchanged. Adds explicitly post-gravity-ramp
motion checks and describes deformation-patch distortion without filtering.
These diagnostics are not pre-registered convergence/physical validation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run, out = args.run_dir.resolve(), args.output_dir.resolve()
    if out.exists():
        raise ValueError('Choose fresh diagnostic directory; preserve prior outputs')
    review = run / 'filled-review-001'
    report = json.loads((review / 'review.json').read_text())
    if report['savedIntegrity'] != 'PASS' or report['nativeComplete']:
        raise ValueError('Requires the actual integrity-checked partial result')
    helper_path = review / 'analysis-source/review-urmi-damage40.py'
    spec = importlib.util.spec_from_file_location('frozen_terminal_helper', helper_path)
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    cfg = report['actualConfig']
    states, velocities, times = [], [], []
    base = None
    for frame, values in helper.csv_frames(review / 'saved-inputs/material-state.csv'):
        pos = np.column_stack([values['x_m'], values['y_m']])
        f = np.column_stack([values[f'F_{i}{j}'] for i in range(3) for j in range(3)]).reshape(-1, 3, 3)
        singular = np.linalg.svd(f, compute_uv=False)
        mass = values['mass_kg_per_m']
        time = float(values['native_time_s'][0])
        if frame == 0:
            initial = pos.copy()
            cohort = (initial[:, 0] > cfg['observerInitialXGreater']) & (initial[:, 1] > cfg['observerInitialYGreater'])
            graph = helper.graph_for(initial, cohort, .2525)
        if time == cfg['gravityRampDuration']:
            base = pos.copy()  # read-only observation reference, NO native reset
        times.append(time)
        velocities.append(values['vx_m_per_s'].copy())
        item = {'frame': frame, 'nativeTimeS': time,
                'maximumSingularStretch': float(singular[:, 0].max()),
                'minimumSingularStretch': float(singular[:, -1].min()),
                'stretch99Percentile': float(np.quantile(singular[:, 0], .99)),
                'countStretchAbove10': int((singular[:, 0] > 10).sum()),
                'centresInsideDomain': bool(((pos >= 0).all(axis=1) & (pos[:, 0] <= cfg['domainWidth']) & (pos[:, 1] <= cfg['domainHeight'])).all()),
                'minimumDomainMarginM': float(values['particle_domain_margin_m'].min()),
                'postRampConnectedMovingUpperMassFraction': 0,
                'postRampPersistence': {'status': 'NOT_EVALUATED'}}
        if base is not None:
            displacement = pos - base
            downhill = displacement @ np.array([np.cos(np.deg2rad(40)), -np.sin(np.deg2rad(40))])
            selected = helper.largest_component(cohort & (displacement[:, 0] >= .25) & (downhill >= .5), graph, mass)
            fraction = float(mass[selected].sum() / mass[cohort].sum()) if len(selected) else 0
            item['postRampConnectedMovingUpperMassFraction'] = fraction
            item['postRampUpperCentroidDisplacementM'] = np.average(displacement[cohort], weights=mass[cohort], axis=0).tolist()
            if fraction >= .1:
                keep = np.array(times) >= cfg['gravityRampDuration']
                mean = np.array([np.average(v[selected], weights=mass[selected]) for v in velocities])
                item['postRampPersistence'] = helper.sustained_interval(np.array(times)[keep], mean[keep],
                    {'minimumSustainedVxMPerS': .001, 'minimumSustainedDurationS': 1})
        states.append(item)
    supported = [s['nativeTimeS'] for s in states if s['postRampPersistence']['status'] == 'PASS']
    out.mkdir(parents=True)
    result = {'scope': 'SAVED_ONLY_POST_RAMP_MOTION_AND_F_DISTORTION_DIAGNOSIS_NOT_PHYSICAL_VALIDATION',
              'solverUpdates': 0, 'reviewReruns': 0, 'renderReruns': 0,
              'originalReviewerUnchanged': True,
              'criteria': 'Existing .25m horizontal/.5m downhill/10% connected upper cohort, persistence vx>.001m/s for1s; here restricted to times>=2s and displacement relative to saved2s state; posthoc diagnostic, not preregistered calibration',
              'numericalSlidingSupportedByPostRampMotion': bool(supported),
              'firstSupportedSavedTimeS': min(supported) if supported else None,
              'nativeComplete': False, 'scientificallyValidated': False,
              'failure': {'condition': 'CL-MPM/ERRORS:ERROR-DF-NEGATIVE',
                          'meaningFromFrozenSource': 'det(I+stretchTensor)<0 guarded before deformation update (fbar disabled); NOT proof saved total J was negative',
                          'failedParticleTupleAvailable': False,
                          'exactFailureReplayPossible': False,
                          'noSyntheticReplacement': True},
              'interpretation': 'Visible unnotched downslope mass motion precedes late severely elongated F-convected patches. Final streaks are retained numerical distortion, not a validated long-distance runout/crack surface. Full20s remains incomplete.',
              'states': states,
              'bindings': {str(p): digest(p) for p in [review / 'review.json', helper_path, review / 'saved-inputs/material-state.csv', run / 'source/src/core/stress-update.lisp', run / 'manifest.json']}}
    (out / 'diagnosis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    (out / 'executed-diagnostic.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'postRampNumericalSlidingSupported': bool(supported), 'firstSupportedSavedTimeS': min(supported) if supported else None, 'finalState': states[-1]}))


if __name__ == '__main__':
    main()
