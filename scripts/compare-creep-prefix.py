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
    parser.add_argument('--allow-increased-update-budget', action='store_true',
                        help='Permit only a declared nondecreasing positive-integer maxUpdates cap; saved-state checks stay byte-exact')
    args = parser.parse_args()
    reference, candidate = args.reference.resolve(), args.candidate.resolve()
    before, after = read(reference / 'manifest.json'), read(candidate / 'manifest.json')
    before_budget, after_budget = (m['config'].get('maxUpdates') for m in (before, after))
    budgets_valid = all(type(value) is int and value > 0 for value in (before_budget, after_budget))
    budget_nondecreasing = budgets_valid and after_budget >= before_budget
    budget_excluded = args.allow_increased_update_budget and budget_nondecreasing
    excluded_keys = {'duration', 'frames'}
    if budget_excluded:
        excluded_keys.add('maxUpdates')
    configs = [{k: v for k, v in m['config'].items() if k not in excluded_keys}
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
    old_loading, new_loading = reference / 'loading-history.csv', candidate / 'loading-history.csv'
    loading_presence = [path.is_file() for path in (old_loading, new_loading)]
    loading_identical = None
    if all(loading_presence):
        old_loading_rows = old_loading.read_bytes().splitlines()
        new_loading_rows = new_loading.read_bytes().splitlines()
        loading_identical = old_loading_rows == new_loading_rows[:len(old_loading_rows)]
    elif any(loading_presence):
        loading_identical = False
    loading_passed = loading_identical is not False
    cadence = [m['config']['duration'] / (m['config']['frames'] - 1) for m in (before, after)]
    passed = (before.get('complete') is True and after.get('complete') is True
              and after['timeS'] >= before['timeS'] and configs[0] == configs[1]
              and (not args.allow_increased_update_budget or budget_nondecreasing)
              and cadence[0] == cadence[1] and bool(records)
              and all(row['identical'] for row in records) and history_identical and loading_passed)
    report = {'passed': passed, 'scope': 'Strict saved-state prefix regression; not scientific failure validation',
              'reference': str(reference), 'candidate': str(candidate),
              'prefixPhysicalTimeS': before['timeS'], 'candidatePhysicalTimeS': after.get('timeS'),
              'physicalConfigurationIdentical': configs[0] == configs[1],
              'allowIncreasedUpdateBudgetRequested': args.allow_increased_update_budget,
              'updateBudgetBefore': before_budget, 'updateBudgetAfter': after_budget,
              'updateBudgetsPositiveIntegers': budgets_valid,
              'updateBudgetNondecreasing': budget_nondecreasing,
              'updateBudgetExcludedFromPhysicalConfigurationComparison': budget_excluded,
              'updateBudgetScope': 'Declared computational update cap only; numerical tolerances and saved-state byte comparisons unchanged',
              'outputCadenceIdentical': cadence[0] == cadence[1],
              'loadingHistoryPresence': {'reference': loading_presence[0], 'candidate': loading_presence[1]},
              'loadingHistoryPrefixByteIdentical': loading_identical,
              'loadingHistoryScope': 'When both exist, exact saved-line prefix including header/contact/work; neither present is not applicable; one-sided presence fails',
              'historyPrefixByteIdentical': history_identical, 'vtk': records,
              'comparisonScriptSha256': digest(Path(__file__))}
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'vtk'}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
