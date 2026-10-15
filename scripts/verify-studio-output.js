'use strict';
// Inspect the particle writer's legacy big-endian binary VTK without solver stubs.
// Usage: node scripts/verify-studio-output.js <ui-output> <export-output> [frames]
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

function readParticleVtk(file) {
  const data = fs.readFileSync(file);
  let offset = 0;
  function line() {
    const end = data.indexOf(10, offset);
    assert.ok(end >= offset, `Missing VTK header newline in ${file} at ${offset}`);
    assert.ok(data.subarray(offset, end).every(byte => byte <= 127), `Non-ASCII VTK header in ${file}`);
    const text = data.toString('latin1', offset, end).replace(/\r$/, '');
    offset = end + 1;
    return text;
  }
  function doubles(count) {
    assert.ok(offset + count * 8 <= data.length, `Truncated binary array in ${file}`);
    const values = [];
    for (let i = 0; i < count; i++, offset += 8) {
      const value = data.readDoubleBE(offset);
      assert.ok(Number.isFinite(value), `Non-finite VTK value in ${file} at ${offset}`);
      values.push(value);
    }
    assert.equal(line(), '', `Binary array must be followed by a newline in ${file}`);
    return values;
  }
  assert.match(line(), /^# vtk DataFile Version /);
  line(); // Human-readable title.
  assert.equal(line(), 'BINARY');
  assert.equal(line(), 'DATASET UNSTRUCTURED_GRID');
  const pointsHeader = line().match(/^POINTS (\d+) double$/);
  assert.ok(pointsHeader, `Unexpected POINTS header in ${file}`);
  const count = Number(pointsHeader[1]);
  assert.ok(count > 0, `Empty particle output in ${file}`);
  const points = doubles(count * 3);
  assert.equal(line(), `POINT_DATA ${count}`);
  const scalars = Object.create(null);
  while (offset < data.length) {
    const header = line();
    if (!header) continue;
    const scalar = header.match(/^SCALARS (\S+) double 1$/);
    assert.ok(scalar, `Unexpected scalar header ${JSON.stringify(header)} in ${file}`);
    assert.ok(!Object.hasOwn(scalars, scalar[1]), `Duplicate scalar ${scalar[1]}`);
    assert.equal(line(), 'LOOKUP_TABLE default');
    scalars[scalar[1]] = doubles(count);
  }
  // Require the whole fixed Studio damage-simulation layout, including its tail.
  // Damage arrays are still written when damage evolution is disabled.
  const fields = ['unique-id', 'mass', 'volume', 'index', 'mpi-index', 'split-depth',
    'fric-contact', 'fric-normal', 'p-wave-modulus', 'yield-function', 'plastic-strain',
    'damage-inc', 'damage', 'damage-ybar', 'damage-ybar-scaled', 'damage-y', 'damage-k', 'damage-length',
    'vel_x', 'vel_y', 'acc_x', 'acc_y', 'disp_x', 'disp_y', 'size_x', 'size_y',
    'sig_xx', 'sig_yy', 'sig_xy', 'eps_xx', 'eps_yy', 'eps_xy', 'size_xx', 'size_yy', 'size_xy', 'size_yx'];
  for (const field of fields)
    assert.ok(scalars[field], `Missing particle field ${field} in ${file}`);
  assert.ok(scalars.mass.every(value => value > 0), `Nonpositive mass in ${file}`);
  return { count, points, scalars };
}

function hash(data) {
  return crypto.createHash('sha256').update(data).digest('hex');
}

function verify(uiDir, exportDir, frames = 3) {
  assert.ok(Number.isInteger(frames) && frames > 0);
  const results = [];
  for (const [folder, extension, prefix] of [['vtk', 'vtk', 'sim'], ['frames', 'png', 'frame']]) {
    const expected = Array.from({ length: frames }, (_, i) => `${prefix}_${String(i + 1).padStart(5, '0')}.${extension}`);
    for (const dir of [uiDir, exportDir])
      assert.deepEqual(fs.readdirSync(path.join(dir, folder)).filter(name => name.startsWith(prefix + '_')).sort(), expected);
    for (const name of folder === 'vtk' ? ['mesh.vtk', ...expected] : expected) {
      const relative = path.join(folder, name);
      const left = fs.readFileSync(path.join(uiDir, relative));
      const right = fs.readFileSync(path.join(exportDir, relative));
      assert.ok(left.length > 0 && left.equals(right), `UI/export bytes differ: ${relative}`);
      let numeric = null;
      if (name.startsWith('sim_')) {
        const vtk = readParticleVtk(path.join(uiDir, relative));
        numeric = { particles: vtk.count, finiteValues: vtk.points.length + Object.values(vtk.scalars).reduce((n, a) => n + a.length, 0), scalarFields: Object.keys(vtk.scalars).length };
      }
      if (extension === 'png') {
        assert.ok(left.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])));
        assert.ok(left.subarray(-12).equals(Buffer.from([0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130])));
      }
      results.push({ file: relative, bytes: left.length, sha256: hash(left), byteIdentical: true, ...(numeric || {}) });
    }
  }
  return { passed: true, frames, uiDir: path.resolve(uiDir), exportDir: path.resolve(exportDir), files: results };
}

if (require.main === module) {
  const [uiDir, exportDir, frames = '3'] = process.argv.slice(2);
  assert.ok(uiDir && exportDir, 'Usage: node scripts/verify-studio-output.js <ui-output> <export-output> [frames]');
  console.log(JSON.stringify(verify(uiDir, exportDir, Number(frames)), null, 2));
}
module.exports = { readParticleVtk, verify };
