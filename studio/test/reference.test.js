'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { normalize } = require('../public/config.js');
const geometry = require('../public/geometry.js');
const workspace = require('../public/model-workspace.js');
const schema = require('../schema.json').parameters;
const presets = require('../reference-presets.json');

test('reference variants preserve the paper modulus conflict and reach API/export without mesh or ductility clamping', () => {
  for (const [name, E] of [['jossProse', 1e9], ['jossTable', 1e8]]) {
    const preset = presets[name];
    const config = normalize(preset.config, schema);
    assert.deepEqual(config, preset.config);
    assert.equal(config.E, E);
    assert.equal(config.scenario, 'joss-bay');
    assert.equal(config.meshSize, 1 / 6);
    assert.equal(config.mpsPerCell, 3);
    assert.equal(config.cohesion, 1965600);
    assert.equal(config.damageCohesion, 26000);
    assert.equal(config.quasiStaticTolerance, 0.01);
    assert.equal(preset.provenance.validated, false);
    assert.match(preset.provenance.modulusConflict, /1 GPa.*100 MPa/);
    const script = workspace.exportRunScript(config);
    assert.match(script, /"scenario" config\) :joss-bay/);
    assert.match(script, /"fractureEnergy" config\) 48d0/);
    assert.match(script, /"simulationTime" config\) 360d0/);
    assert.match(script, /"geometryRefinement" config\) 4/);
  }
  assert.ok(presets.jossProse.config.ductility > 500);
  assert.ok(presets.jossTable.config.ductility < 60);
});

test('Joss geometry has a 31 m domain, 1 m foundation, vertical upper face and a 45 degree notch', () => {
  const g = geometry.dimensions(presets.jossProse.config);
  assert.equal(g.width, 31);
  assert.equal(g.top, 16.5);
  const kink = 1 + 15.5 - 6.8;
  // The measured video upper face is around x=13.6 m (image uncertainty ~0.1 m).
  assert.ok(Math.abs(geometry.faceX(g, kink) - 13.6) < 0.1);
  assert.equal(geometry.faceX(g, 16.4), geometry.faceX(g, kink));
  assert.equal(geometry.materialContains(g, 30, 0.5), true);
  assert.equal(geometry.materialContains(g, 15.1, 1.01), false);
  assert.equal(geometry.materialContains(g, 14.9, 1.01), true);
  assert.equal(geometry.notchContains(g, 15.3, 1.1), true);
  assert.equal(geometry.notchContains(g, 15.3, 1.4), false);
});

test('normal Studio defaults remain selected and custom/reference combinations fail before export', () => {
  const defaults = normalize({}, schema);
  assert.equal(defaults.scenario, 'studio-cliff');
  assert.equal(defaults.meshSize, 5);
  assert.equal(defaults.shelfHeight, 100);
  assert.equal(defaults.E, 1e9);
  assert.equal(defaults.maxSteps, 10);
  assert.throws(() => workspace.exportRunScript({...presets.jossProse.config, constitutiveModel:'custom'}), /dedicated reference material/);
});
