"""Plot actual held-stress material-point evidence; not a slope/laboratory result."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory', required=True, type=Path)
args = parser.parse_args()
fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
for name, label in [('constant-strength-hold.csv', 'Constant strength'),
                    ('softening-hold.csv', 'Strain softening')]:
    with (args.directory / name).open(newline='', encoding='utf-8-sig') as stream:
        rows = [{k: float(v.lower().replace('d', 'e')) for k, v in row.items()}
                for row in csv.DictReader(stream)]
    times = [r['time_s'] for r in rows]
    for ax, key in zip(axes, ['strain_percent', 'rate_per_s', 'q_kirchhoff_pa']):
        factor = .001 if key.endswith('_pa') else 1
        ax.plot(times, [r[key] * factor for r in rows], label=label)
for ax, label in zip(axes, ['Accumulated equivalent creep strain (%)',
                          'Equivalent creep rate (1/s)', 'Held q (kPa, Kirchhoff)']):
    ax.set(xlabel='Physical hold time (s)', ylabel=label)
    ax.grid(alpha=.25)
axes[0].legend()
fig.suptitle('Native material-point hold: computed creep under sustained stress\n'
             'Explicit demonstration parameters; no lab calibration or slope-failure claim')
fig.savefig(args.directory / 'material-creep-hold.png', dpi=150)
print(args.directory / 'material-creep-hold.png')
