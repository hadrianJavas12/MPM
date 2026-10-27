"""Freeze the gated physical case, native bytes and postprocessors before launch."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'output/urmi-mc-damage40-2026-10-27/full-001'
GATE = ROOT / 'output/urmi-mc-damage40-2026-10-27/pipeline-001'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def record(path):
    data = path.read_bytes()
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def main():
    assert not RUN.exists() and not Path(str(RUN)+'-status.json').exists()
    assert read(GATE/'result.json')['passed'] is True
    assert read(GATE.parent/'pipeline-001.exit.json')['exitCode'] == 0
    assert read(GATE.parent/'pipeline-saved-audit-002/review.json')['passed'] is True
    prep = Path(str(RUN)+'-launch-preparation')
    prep.mkdir(parents=True, exist_ok=False)
    copies, expected = [], []
    omitted = {'source/inputs/research/notes/urmi-mc-damage40-2026-10-26/recipe-plan.md',
               'source/inputs/cases/benchmarks/urmi-damage40.lisp'}
    for row in read(GATE/'source/source-manifest.json')['files']:
        relative = row['path'].replace('\\', '/')
        if relative in omitted:
            continue
        original = ROOT/'cases/benchmarks/urmi-damage40.lisp' if relative == 'source/case.lisp' else Path(row['originalPath'])
        actual = record(original)
        if relative != 'source/case.lisp':
            assert (actual['bytes'], actual['sha256']) == (row['bytes'], row['sha256']), relative
        target = prep/'native-expected'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        assert original.read_bytes() == target.read_bytes()
        expected.append(dict(path=relative, bytes=actual['bytes'], sha256=actual['sha256']))
    for relative, folder in [('scripts/review-urmi-damage40.py', 'analysis'),
                             ('scripts/plot_m5_cliff_comparison.py', 'analysis'),
                             ('research/references/urmi-mc-damage40/contract.json', 'protocol'),
                             ('research/notes/urmi-mc-damage40-2026-10-26/recipe-plan.md', 'protocol'),
                             ('scripts/start-wang2017-detached.ps1', 'wrapper'),
                             ('scripts/run-gravity-slope-trial.ps1', 'wrapper'),
                             ('scripts/prepare-urmi-damage40-launch.py', 'preparation')]:
        original = ROOT/relative
        copy = prep/folder/original.name
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, copy)
        assert original.read_bytes() == copy.read_bytes()
        copies.append(dict(original=record(original), copy=record(copy)))
    proof = dict(preparedUtc=datetime.now(timezone.utc).isoformat(),
                 sourceCommit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                 runDirectory=str(RUN), maxWallHours=48, requestedDynamicSeconds=60,
                 expectedNativeFiles=expected, support=copies,
                 scope='All gated native bytes unchanged except declared gate test→full case. Excludes two gate-only inputs. No solver invocation.',
                 wrapperLabel='Unchanged gravity-slope wrapper family; actual native scenario is urmi-damage40',
                 limitation='CIM user session is not proven immune to logoff, sleep or reboot; wall cap is not ETA')
    (prep/'preparation.json').write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(prepared=True, nativeFiles=len(expected), supportFiles=len(copies), sourceCommit=proof['sourceCommit'])))


if __name__ == '__main__':
    main()
