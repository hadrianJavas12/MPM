"""ONE exact saved prefix comparison; no native, replay, audit or renderer."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import traceback

import numpy as np
import plot_m5_cliff_comparison as reader

EXTRA_VTK = {'mc-apex-active-last', 'mc-apex-lambda-last'}


def record(path):
    payload = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(payload),
            'sha256': hashlib.sha256(payload).hexdigest()}


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def number(value):
    result = float(value.replace('d', 'e').replace('D', 'E'))
    if not math.isfinite(result):
        raise ValueError('Nonfinite compared CSV value')
    return result


def integer(value):
    result = number(value)
    if result != round(result):
        raise ValueError('Nonintegral compared identity')
    return int(result)


def prefix_csv(path, cutoff, particle):
    rows, order, raw = {}, [], []
    with path.open('rb') as stream:
        header_bytes = stream.readline()
        header = next(csv.reader([header_bytes.decode('utf-8-sig').rstrip('\r\n')]))
        if len(set(header)) != len(header):
            raise ValueError('Duplicate CSV header')
        previous_time = -1.
        for line in stream:
            cells = next(csv.reader([line.decode('utf-8').rstrip('\r\n')]))
            if len(cells) != len(header):
                raise ValueError('CSV row/header width differs')
            row = dict(zip(header, cells))
            time = number(row['time_s'])
            if time < previous_time:
                raise ValueError('CSV time order is not monotone')
            previous_time = time
            if time > cutoff:
                break
            key = (time, integer(row['particle_id'])) if particle else (time,)
            if key in rows:
                raise ValueError('Duplicate actual-time/ID key')
            rows[key] = row
            order.append(key)
            raw.append(line)
    return {'header': header, 'headerBytes': header_bytes, 'rows': rows,
            'order': order, 'rawPrefix': header_bytes + b''.join(raw)}


def compare_csv(old_path, new_path, cutoff, particle):
    old, new = (prefix_csv(path, cutoff, particle) for path in (old_path, new_path))
    old_keys, new_keys = set(old['rows']), set(new['rows'])
    common_keys = sorted(old_keys & new_keys)
    common_columns = [name for name in old['header'] if name in new['header']]
    strings = numeric = bits = compared = 0
    maxima = {name: 0. for name in common_columns}
    examples = []
    for key in common_keys:
        for name in common_columns:
            left, right = old['rows'][key][name], new['rows'][key][name]
            a, b = number(left), number(right)
            different_string = left != right
            different_numeric = a != b
            different_bits = struct.pack('>d', a) != struct.pack('>d', b)
            strings += different_string
            numeric += different_numeric
            bits += different_bits
            compared += 1
            maxima[name] = max(maxima[name], abs(a - b))
            if (different_string or different_bits) and len(examples) < 12:
                examples.append({'key': list(key), 'column': name, 'strictString': left,
                    'compositeString': right, 'absoluteFloatDifference': abs(a - b),
                    'floatBitsDiffer': different_bits})
    prefixes_equal = old['rawPrefix'] == new['rawPrefix']
    result = {'strictInput': record(old_path), 'compositeInput': record(new_path),
        'strictPrefixRows': len(old_keys), 'compositePrefixRows': len(new_keys),
        'commonActualTimeIdRows': len(common_keys), 'scalarValuesCompared': compared,
        'strictOnlyKeys': [list(key) for key in sorted(old_keys - new_keys)],
        'compositeOnlyKeys': [list(key) for key in sorted(new_keys - old_keys)],
        'rowOrderIdentical': old['order'] == new['order'],
        'headerBytesIdentical': old['headerBytes'] == new['headerBytes'],
        'commonColumns': common_columns, 'strictOnlyColumns': sorted(set(old['header']) - set(new['header'])),
        'compositeOnlyColumns': sorted(set(new['header']) - set(old['header'])),
        'prefixRawBytesIdentical': prefixes_equal,
        'strictPrefixBytes': len(old['rawPrefix']), 'compositePrefixBytes': len(new['rawPrefix']),
        'strictPrefixSha256': hashlib.sha256(old['rawPrefix']).hexdigest(),
        'compositePrefixSha256': hashlib.sha256(new['rawPrefix']).hexdigest(),
        'stringDifferences': strings, 'numericFloatDifferences': numeric,
        'ieeeFloatBitDifferences': bits, 'maximumAbsoluteDifferenceByColumn': maxima,
        'firstDifferences': examples}
    result['allPrefixChecksExact'] = (prefixes_equal and old_keys == new_keys
        and old['order'] == new['order'] and old['header'] == new['header'] and strings == numeric == bits == 0)
    return result, old, new


def arrays(old, new):
    a, b = (np.ascontiguousarray(value, dtype=np.float64) for value in (old, new))
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Nonfinite compared VTK value')
    if a.shape != b.shape:
        return {'shapeIdentical': False, 'strictShape': list(a.shape), 'compositeShape': list(b.shape),
                'allFloatBitsIdentical': False}
    different = a.view(np.uint64) != b.view(np.uint64)
    return {'shapeIdentical': True, 'valuesCompared': int(a.size),
        'numericFloatDifferences': int(np.count_nonzero(a != b)),
        'ieeeFloatBitDifferences': int(np.count_nonzero(different)),
        'maximumAbsoluteDifference': float(np.abs(a - b).max()) if a.size else 0.,
        'firstDifferentIndices': np.argwhere(different)[:3].tolist(),
        'allFloatBitsIdentical': not bool(different.any())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir', required=True, type=Path)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    old_run, new_run, output = (path.resolve() for path in (args.reference_dir, args.run_dir, args.output_dir))
    if (output / 'result.json').exists():
        raise RuntimeError('Comparison result already exists; do not repeat')
    support = Path(__file__).resolve().parent
    if support != (output / 'analysis-support').resolve() or Path(reader.__file__).resolve().parent != support:
        raise RuntimeError('Comparator and reader must execute from copied analysis-support')
    before = read_json(output / 'analysis-source-before.json')
    for row in before:
        if record(Path(row['path']))['sha256'] != row['sha256']:
            raise RuntimeError('Comparison source changed before execution')
    report = {'schema': 'cl-mpm.gravity-composite.strict-prefix.v1',
        'createdUtc': datetime.now(timezone.utc).isoformat(),
        'landslideVerified': False, 'scientificallyValidated': False,
        'referenceDirectory': str(old_run), 'compositeDirectory': str(new_run),
        'comparisonPolicy': 'Exact actual time/ID matching, raw/string/numeric/IEEE-bit equality; no interpolation or tolerance',
        'sourceBefore': before, 'csv': {}, 'vtkFrames': []}
    try:
        old_manifest, new_manifest = (read_json(path / 'manifest.json') for path in (old_run, new_run))
        cutoff = old_manifest.get('lastSavedTimeS', old_manifest['timeS'])
        if cutoff != 1.7 or old_manifest['savedFrames'] != 18:
            raise ValueError('Reference differs from the authorized 18-state/1.7s prefix')
        report.update(lastReferenceSavedTimeS=cutoff, referenceAttemptTimeS=old_manifest.get('attemptTimeS'),
            referenceNativeComplete=old_manifest['complete'], compositeNativeComplete=new_manifest['complete'],
            scope='Only saved0–1.7s/18states. No extrapolation to the later unsaved strict failure or the new post-apex trajectory.',
            manifests=[record(path / 'manifest.json') for path in (old_run, new_run)])
        for filename, particle in (('history.csv', False), ('particles.csv', True)):
            comparison, old, new = compare_csv(old_run / filename, new_run / filename, cutoff, particle)
            report['csv'][filename] = comparison
            if not particle:
                history_old, history_new = old, new
        times = [key[0] for key in history_old['order']]
        if len(times) != 18:
            raise ValueError('Reference actual history does not contain18prefix states')
        all_vtk = True
        for time in times:
            key = (time,)
            if key not in history_new['rows']:
                all_vtk = False
                report['vtkFrames'].append({'timeS': time, 'status': 'NO_EXACT_COMPOSITE_TIME_MATCH'})
                continue
            old_frame = integer(history_old['rows'][key]['frame'])
            new_frame = integer(history_new['rows'][key]['frame'])
            old_path = old_run / 'vtk' / f'particles_{old_frame:04d}.vtk'
            new_path = new_run / 'vtk' / f'particles_{new_frame:04d}.vtk'
            old_positions, old_fields = reader.read_cliff_vtk(old_path)
            new_positions, new_fields = reader.read_cliff_vtk(new_path)
            common = sorted(set(old_fields) & set(new_fields))
            removed, extra = sorted(set(old_fields) - set(new_fields)), sorted(set(new_fields) - set(old_fields))
            fields = {name: arrays(old_fields[name], new_fields[name]) for name in common}
            positions = arrays(old_positions, new_positions)
            exact = (not removed and set(extra) == EXTRA_VTK and positions['allFloatBitsIdentical']
                     and all(value['allFloatBitsIdentical'] for value in fields.values())
                     and 'unique-id' in common)
            all_vtk = all_vtk and exact
            report['vtkFrames'].append({'timeS': time, 'strictFrame': old_frame, 'compositeFrame': new_frame,
                'strictInput': record(old_path), 'compositeInput': record(new_path),
                'rawCompleteFilesByteIdentical': old_path.read_bytes() == new_path.read_bytes(),
                'rawFileDifferenceExpectedFromExtraFields': True, 'positions': positions, 'commonFields': fields,
                'removedFields': removed, 'newFields': extra,
                'newFieldRanges': {name: {'min': float(np.min(new_fields[name])), 'max': float(np.max(new_fields[name]))}
                                   for name in extra}, 'allCommonParsedFieldsExact': exact})
        report['allCommonPrefixStatesExact'] = all_vtk and all(row['allPrefixChecksExact'] for row in report['csv'].values())
        report['status'] = 'PASS_EXACT_COMMON_PREFIX' if report['allCommonPrefixStatesExact'] else 'FAIL_STRICT_PREFIX_EQUALITY'
    except Exception as error:
        report['status'] = 'ERROR'
        report['error'] = f'{type(error).__name__}: {error}'
        (output / 'failure-traceback.txt').write_text(traceback.format_exc(), encoding='utf-8')
    report['analysisSourceAfterMatch'] = all(record(Path(row['path']))['sha256'] == row['sha256'] for row in before)
    if not report['analysisSourceAfterMatch']:
        report['status'] = 'ERROR_SOURCE_CHANGED'
    (output / 'result.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'vtkFrames': len(report['vtkFrames']),
        'csv': {name: {key: value for key, value in row.items() if key in
          ('commonActualTimeIdRows', 'prefixRawBytesIdentical', 'stringDifferences', 'numericFloatDifferences', 'ieeeFloatBitDifferences')}
                for name, row in report['csv'].items()}, 'error': report.get('error')}, indent=2))
    return 0 if report['status'] == 'PASS_EXACT_COMMON_PREFIX' else 1


if __name__ == '__main__':
    sys.exit(main())
