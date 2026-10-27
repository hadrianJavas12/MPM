"""Independent read of the FIRST bounded native pipeline, without more MPM."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--frozen', action='store_true')
    args = parser.parse_args()
    run, out = args.run_dir.resolve(), args.output_dir.resolve()
    if not args.frozen:
        out.mkdir(parents=True, exist_ok=False)
        support = out / 'analysis-source'
        support.mkdir()
        files = [Path(__file__), Path(__file__).with_name('review-urmi-damage40.py'),
                 Path(__file__).with_name('plot_m5_cliff_comparison.py'),
                 Path(__file__).resolve().parents[1] / 'research/references/urmi-mc-damage40/contract.json']
        import hashlib
        records = []
        for file in files:
            copy = support / file.name
            shutil.copyfile(file, copy)
            assert file.read_bytes() == copy.read_bytes()
            records.append(dict(original=str(file), copy=str(copy), sha256=hashlib.sha256(copy.read_bytes()).hexdigest()))
        (out / 'analysis-freeze.json').write_text(json.dumps(records, indent=2))
        command = [sys.executable, str(support / Path(__file__).name), '--run-dir', str(run), '--output-dir', str(out), '--frozen']
        (out / 'command.json').write_text(json.dumps(command, indent=2))
        with (out / 'stdout.log').open('w') as stdout, (out / 'stderr.log').open('w') as stderr:
            result = subprocess.run(command, stdout=stdout, stderr=stderr)
        (out / 'exit.json').write_text(json.dumps(dict(exitCode=result.returncode)))
        return result.returncode
    import importlib.util
    spec = importlib.util.spec_from_file_location('owned_review', Path(__file__).with_name('review-urmi-damage40.py'))
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    from plot_m5_cliff_comparison import read_cliff_vtk
    contract = review.load_json(Path(__file__).with_name('contract.json'))
    native = review.load_json(run / 'result.json')
    assert native['passed'] is True and len(native['passedGroups']) == 4
    source = review.verified_sources(run)
    review.verify_law_source(run, contract['material'])
    nodes, bound = review.reference_table(contract['material'])
    history = review.history_rows(run / 'history.csv')
    baseline, previous, states = None, None, []
    for frame, values in review.csv_frames(run / 'material-state.csv'):
        assert frame == len(states) and frame in history
        if frame == 2:
            # This bounded gate saves AFTER two dynamic updates, not a separate
            # phase2 release frame. Bind origins to the actual native ledger
            # and saved drained history without fabricating a missing state.
            origins = np.array([entry['kappaOrigin'] for entry in native['observations']['ledger']])
            assert review.close(origins, previous['mc_kappa'])
            assert np.array_equal(values['kappa_origin'], origins)
            baseline['origin'] = origins
        baseline, state, pos, _, _ = review.audit_frame(values, history[frame], run / f'particles_{frame:04d}.vtk',
             read_cliff_vtk, baseline, previous, (0, 1, 3)[frame], contract, source['constants'], nodes)
        states.append(state)
        previous = {key: values[key].copy() for key in ('mc_kappa', 'plastic_work_pa')}
        if frame == 0:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            figure, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)
            points = ax.scatter(pos[:, 0], pos[:, 1], c=values['strength_damage'], vmin=0, vmax=1,
                                cmap='inferno', s=5, linewidths=0)
            ax.axhline(4, color='steelblue', linestyle=':', label='4m active soil foundation')
            ax.set(xlim=(-.5, 60.5), ylim=(-.5, 20.5), xlabel='x (m)', ylabel='y (m)',
                   title='ACTUAL initial native particles: 40 degree slope, no notch; D_s inactive during drained preparation')
            ax.set_aspect('equal')
            ax.legend()
            figure.colorbar(points, ax=ax, label='Strength loss D_s, fixed 0–1')
            figure.savefig(out / 'actual-initial-geometry.png', dpi=150)
            plt.close(figure)
    assert len(states) == len(history) == 3
    n = states[0]['particleCount']
    assert n == native['observations']['particleCount']
    assert native['nativeMpmUpdatesAccepted'] == 4
    assert native['drainedConstitutiveAccepted'] == native['undrainedConstitutiveAccepted'] == 2*n
    assert native['instantaneousTransferConstitutiveAccepted'] == n
    report = dict(passed=True, actualFrames=3, particleRows=3*n, particleCount=n, sourceProof=source,
                  tableBoundPa=bound, states=states, scientificValidation=False,
                  scope='Bounded saved output only; no actual equilibrium, full orchestration, damage onset or slope validation')
    review.write_json(out / 'review.json', report)
    print(json.dumps(dict(passed=True, particleCount=n, particleRows=3*n, actualFrames=3)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
