"""Strictly compare a longer creep run's saved prefix with its completed baseline."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reference, candidate = args.reference.resolve(), args.candidate.resolve()
    before, after = read(reference / 'manifest.json'), read(candidate / 'manifest.json')
    configs = [{k: v for k, v in m['config'].items() if k not in ('duration', 'frames')}
               for m in (before, after)]
    records = []
    for path in sorted((reference / 'vtk').glob('*.vtk')):
        relative = path.relative_to(reference)
        source_hash, new_hash = digest(path), digest(candidate / relative)
        records.append({'path': relative.as_posix(), 'referenceSha256': source_hash,
                        'candidateSha256': new_hash, 'identical': source_hash == new_hash})
    old_rows = (reference / 'creep-history.csv').read_bytes().splitlines()
    new_rows = (candidate / 'creep-history.csv').read_bytes().splitlines()
    history_identical = old_rows == new_rows[:len(old_rows)]
    cadence = [m['config']['duration'] / (m['config']['frames'] - 1) for m in (before, after)]
    passed = (before.get('complete') is True and after.get('complete') is True
              and after['timeS'] >= before['timeS'] and configs[0] == configs[1]
              and cadence[0] == cadence[1] and bool(records)
              and all(row['identical'] for row in records) and history_identical)
    report = {'passed': passed, 'scope': 'Strict saved-state prefix regression; not scientific failure validation',
              'reference': str(reference), 'candidate': str(candidate),
              'prefixPhysicalTimeS': before['timeS'], 'candidatePhysicalTimeS': after.get('timeS'),
              'physicalConfigurationIdentical': configs[0] == configs[1],
              'outputCadenceIdentical': cadence[0] == cadence[1],
              'historyPrefixByteIdentical': history_identical, 'vtk': records,
              'comparisonScriptSha256': digest(Path(__file__))}
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'vtk'}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
