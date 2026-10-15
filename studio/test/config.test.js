'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { normalize } = require('../public/config.js');
const schema = require('../schema.json').parameters;

test('normalization rejects non-object payloads and does not coerce arrays or booleans into numbers', () => {
  for (const input of [null, 1, 'x', []]) assert.throws(() => normalize(input, schema), /object/);
  const result = normalize({ cohesion: [], soilBoundary: true, density: '0x10' }, schema);
  assert.equal(result.cohesion, schema.cohesion.default);
  assert.equal(result.soilBoundary, schema.soilBoundary.default);
  assert.equal(result.density, schema.density.default);
});

test('missing or invalid fields use defaults; decimal strings, zeros and boolean false survive', () => {
  const result = normalize({ E: ' 1e9 ', cohesion: 0, enableDamage: 'false', enablePlasticity: 'invalid', workers: 2.5 }, schema);
  assert.equal(result.E, 1e9);
  assert.equal(result.cohesion, 0);
  assert.equal(result.enableDamage, false);
  assert.equal(result.enablePlasticity, true);
  assert.equal(result.workers, 3);
});
