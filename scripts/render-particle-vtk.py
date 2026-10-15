#!/usr/bin/env python3
"""Render computed particle domains/damage, with a fixed physical viewport.

This is a scientific data plot; no displacement or damage is invented.
Requires Pillow/numpy and the adjacent reference VTK reader.
"""
import argparse
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

reader_spec = importlib.util.spec_from_file_location('reference_vtk_reader', Path(__file__).with_name('compare-reference-video.py'))
reader_module = importlib.util.module_from_spec(reader_spec)
reader_spec.loader.exec_module(reader_module)
read_particle_vtk = reader_module.read_particle_vtk


def render(args):
    points, fields = read_particle_vtk(args.vtk)
    damage = fields.get('damage', np.zeros(len(points)))
    if (damage < 0).any() or (damage > 1).any():
        raise ValueError('Damage must be in [0, 1]')
    font_path = Path('C:/Windows/Fonts/arial.ttf')
    def font(size):
        return ImageFont.truetype(str(font_path), size) if font_path.exists() else ImageFont.load_default()
    image = Image.new('RGB', (1280, 720), 'white')
    draw = ImageDraw.Draw(image)
    x0, y0, scale = 72., 660., 32.5
    # A fixed blue/cyan/yellow/red scale keeps colour comparable across frames.
    anchors = np.array([[0, 0, 128], [0, 128, 255], [0, 255, 255], [255, 255, 0], [255, 0, 0]], dtype=float)
    def colour(value):
        u = min(4., max(0., float(value) * 4.))
        index = min(3, int(u))
        rgb = anchors[index] * (1 - (u - index)) + anchors[index + 1] * (u - index)
        return tuple(int(x) for x in rgb)
    draw.text((72, 18), args.title, font=font(24), fill='black')
    draw.text((72, 50), f't = {args.time:.3f} s   {args.phase.upper()}   {len(points):,} material points', font=font(19), fill='black')
    sx, sy = fields['size_x'], fields['size_y']
    for point, width, height, value in zip(points, sx, sy, damage):
        x, y = point[:2]
        box = (x0 + scale * (x - width/2), y0 - scale * (y + height/2),
               x0 + scale * (x + width/2), y0 - scale * (y - height/2))
        if args.particle_shape == 'rectangle':
            draw.rectangle(box, fill=colour(value))
        else:
            draw.ellipse(box, fill=colour(value))
    draw.rectangle((x0, y0 - scale * args.ymax, x0 + scale * args.xmax, y0), outline='black', width=1)
    for x in range(0, int(args.xmax) + 1, 5):
        px = x0 + scale * x
        draw.line((px, y0, px, y0 + 5), fill='black')
        draw.text((px - 7, y0 + 8), str(x), font=font(16), fill='black')
    for y in range(0, int(args.ymax) + 1, 5):
        py = y0 - scale * y
        draw.line((x0 - 5, py, x0, py), fill='black')
        draw.text((x0 - 32, py - 8), str(y), font=font(16), fill='black')
    draw.text((535, 697), 'x (m)', font=font(17), fill='black')
    draw.text((8, 355), 'y (m)', font=font(17), fill='black')
    for i in range(400):
        draw.line((1130, 180 + i, 1160, 180 + i), fill=colour(1 - i/399))
    draw.text((1110, 140), 'Damage', font=font(18), fill='black')
    for value in [0., .25, .5, .75, 1.]:
        draw.text((1166, 572 - value * 399), f'{value:g}', font=font(16), fill='black')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    summary = {'vtk': str(args.vtk.resolve()), 'particles': len(points), 'massPerUnitDepth': float(fields['mass'].sum()),
               'damageMax': float(damage.max()), 'massWeightedDamage': float((fields['mass'] * damage).sum()/fields['mass'].sum()),
               'physicalTime': args.time, 'phase': args.phase,
               'renderer': f'{args.particle_shape} computed domains; fixed damage scale [0,1]',
               'collapseValidated': False}
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--vtk', type=Path)
    inputs.add_argument('--run-dir', type=Path, help='Render recorded physical frames using timesteps.csv')
    parser.add_argument('--output', type=Path, required=True, help='PNG path, or a frame directory with --run-dir')
    parser.add_argument('--title', default='Computed MPM particle state')
    parser.add_argument('--time', type=float, default=0.)
    parser.add_argument('--phase', default='SETTLE')
    parser.add_argument('--particle-shape', choices=['ellipse', 'rectangle'], default='ellipse',
                        help='Rectangle matches the recovered video renderer; uses actual VTK domain sizes')
    parser.add_argument('--xmax', type=float, default=31.)
    parser.add_argument('--ymax', type=float, default=17.3333333333)
    args = parser.parse_args()
    if args.run_dir:
        summaries = []
        with (args.run_dir / 'timesteps.csv').open(newline='') as stream:
            for row in csv.DictReader(stream):
                if row['phase'] == 'settle':
                    continue
                step = int(row['step'])
                frame_args = argparse.Namespace(**vars(args))
                frame_args.vtk = args.run_dir / 'vtk' / f'sim_{step:05d}.vtk'
                frame_args.output = args.output / f'frame_{step:05d}.png'
                frame_args.time = float(row['time'])
                frame_args.phase = row['phase']
                summaries.append(render(frame_args))
        if not summaries:
            raise ValueError('No recorded physical simulation frames')
        (args.output / 'render-summary.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')
        print(json.dumps({'frames': len(summaries), 'last': summaries[-1]}, indent=2))
    else:
        print(json.dumps(render(args), indent=2))


if __name__ == '__main__':
    main()
