'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { validateConfig } = require('../server.js');

test('material controls preserve original chalk defaults', () => {
  const config = validateConfig({});
  assert.equal(config.enablePlasticity, true);
  assert.equal(config.cohesion, 1e6);
  assert.equal(config.dilatancyAngle, 0);
  assert.ok(Math.abs(config.nonlocalLength - 3 * Math.sqrt(7)) < 1e-12);
});

test('zero cohesion and disabled plasticity are valid and not reset', () => {
  const config = validateConfig({
    cohesion: 0, dilatancyAngle: 0, enablePlasticity: false, enableDamage: false,
  });
  assert.equal(config.cohesion, 0);
  assert.equal(config.dilatancyAngle, 0);
  assert.equal(config.enablePlasticity, false);
  assert.equal(config.enableDamage, false);
});

test('material controls clamp numeric values and ignore strings that are not numbers', () => {
  const config = validateConfig({
    cohesion: -100, dilatancyAngle: 99, nonlocalLength: -5,
  });
  assert.equal(config.cohesion, 0);
  assert.equal(config.dilatancyAngle, 45);
  assert.equal(config.nonlocalLength, 0.05);
  assert.equal(validateConfig({ cohesion: 'bad' }).cohesion, 1e6);
});
