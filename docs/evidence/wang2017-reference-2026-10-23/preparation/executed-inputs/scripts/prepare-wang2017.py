"""Audit native Wang inputs and assemble a preparation report; never run a solver."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(native_path, output):
    contract_path = ROOT / 'research/references/wang2017/mpm-reference-contract.json'
    contract, native = read(contract_path), read(native_path)
    if not native['passed'] or native['physicalUpdatesExecuted'] != 0:
        raise ValueError('Expected successful preparation controls without solver updates')
    checks = []

    def check(name, actual, expected):
        if isinstance(expected, (int, float)):
            passed = (isinstance(actual, (int, float)) and not isinstance(actual, bool)
                      and math.isfinite(actual)
                      and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8))
        else:
            passed = actual == expected
        checks.append({'name': name, 'actual': actual, 'reference': expected, 'passed': passed})

    for label in ('full', 'pilot'):
        material, config = native[label + 'Material'], native[label + 'Config']
        for key, expected in contract['soil1'].items():
            if key in ('source', 'model'):
                continue
            check(f'{label}.material.{key}', material.get(key), expected)
        for key, expected in {
            'width': contract['geometry']['widthM'],
            'baseHeight': contract['geometry']['baseThicknessM'],
            'crestLength': contract['geometry']['crestLengthM'],
            'slope': contract['geometry']['slopeDeg'],
            'patchStart': contract['geometry']['patchStartM'],
            'patchLength': contract['geometry']['patchLengthM'],
            'velocity': contract['loading']['velocityMPerS'],
        }.items():
            check(f'{label}.config.{key}', config.get(key), expected)
    check('full.duration', native['fullConfig']['duration'], 1000.0)
    check('pilot.duration', native['pilotConfig']['duration'], 1.0)
    check('height.explicitAssumption', native['fullConfig']['height'], 10.0)
    passed = all(row['passed'] for row in checks)
    report = {
        'paperInputChecksPassed': passed, 'checks': checks,
        'scope': 'Actual native Soil1 input preparation; not a simulated curve or scientific validation',
        'fullSimulationStarted': False, 'referenceAgreementVerified': False,
        'soil2ImplementationStatus': contract['soil2']['implementationStatus'],
        'readiness': 'PAPER_INPUTS_PREPARED_WITH_OPEN_GATES' if passed else 'INPUT_MISMATCH',
        'methodDecision': contract['methodDecision'], 'openGates': contract['openGates'],
        'inputSha256': {'contract': digest(contract_path), 'nativeExport': digest(native_path)},
        'sourceScriptSha256': digest(Path(__file__)),
    }
    if output.exists():
        raise ValueError('Preparation report path must be fresh')
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('checks', 'openGates')}, indent=2))
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    return prepare(args.native_export.resolve(), args.output.resolve())


if __name__ == '__main__':
    raise SystemExit(main())
