"""Retain completed or failed native creep evidence with honest status and hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def pack(destination, base, paths):
    with tarfile.open(destination, 'w:gz') as archive:
        for path in sorted(paths):
            archive.add(path, arcname=path.relative_to(base).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    run, dest = args.run_dir.resolve(), args.destination.resolve()
    run.relative_to(ROOT / 'output')
    dest.relative_to(ROOT / 'docs/evidence')
    status = read(run.parent / (run.name + '-status.json'))
    manifest = read(run / 'manifest.json')
    if status['status'] in ('STARTING', 'NATIVE_RUNNING', 'POSTPROCESSING'):
        raise ValueError('Do not archive a changing run as a final checkpoint')
    audit_path = run / 'output-audit.json'
    audit = read(audit_path) if audit_path.exists() else {}
    if audit.get('nativeComplete') and not manifest.get('complete'):
        raise ValueError('Audit and native completion contradict each other')
    dest.mkdir(parents=True, exist_ok=False)
    (dest / '.gitattributes').write_text('* -text -whitespace\n*.gz binary\n')
    for name in ['manifest.json', 'source-provenance.json', 'output-audit.json',
                 'creep-overview.png', 'creep-diagnostics.png', 'slope-creep.mp4']:
        if (run / name).exists():
            shutil.copyfile(run / name, dest / name)
    pack(dest / 'native-output.tar.gz', run,
         [p for p in run.rglob('*') if p.is_file() and 'source' not in p.relative_to(run).parts
          and 'rendered-frames' not in p.relative_to(run).parts and p.suffix not in ('.png', '.mp4')])
    pack(dest / 'executed-source.tar.gz', run / 'source',
         [p for p in (run / 'source').rglob('*') if p.is_file() and '.native-cache' not in p.parts])
    pack(dest / 'launch-and-logs.tar.gz', run.parent,
         [p for p in run.parent.glob(run.name + '*') if p.is_file()])
    support = dest / 'support'
    support.mkdir()
    for name in ['plot-slope-creep.py', 'plot_m5_cliff_comparison.py', 'collect-slope-creep-evidence.py']:
        shutil.copyfile(ROOT / 'scripts' / name, support / name)
    (dest / 'summary.json').write_text(json.dumps({
        'sourceCommitAtNativeLaunch': status['sourceCommitAtLaunch'],
        'nativeExitCode': status.get('nativeExitCode'), 'nativeComplete': bool(manifest.get('complete')),
        'wrapperStatus': status['status'], 'physicalTimeS': manifest.get('timeS'),
        'savedOutputConsistency': audit.get('passedConsistencyChecks', 'NOT_RUN'),
        'creepObserved': audit.get('creepObserved', 'NOT_REVIEWED'),
        'landslideVerified': False, 'scientificValidation': False,
        'scope': 'Experimental total-stress clay demonstration, not Wang2017 reproduction or laboratory calibration'
    }, indent=2) + '\n')
    entries = [{'path': p.relative_to(dest).as_posix(), 'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(dest.rglob('*')) if p.is_file()]
    (dest / 'evidence-manifest.json').write_text(json.dumps({'entries': entries}, indent=2) + '\n')
    assert all(hashlib.sha256((dest / e['path']).read_bytes()).hexdigest() == e['sha256'] for e in entries)
    print(json.dumps({'verifiedArtifacts': len(entries), 'path': str(dest)}))


if __name__ == '__main__':
    main()
