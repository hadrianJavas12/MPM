'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const g = require('../public/geometry.js');

const base = {
  shelfHeight: 100, shelfAspect: 2, cliffSlope: 90, undercut: 0,
  soilBoundary: 20, notchHeight: 20, notchDepth: 30,
  notchShape: 'rectangle', notchTipFraction: 0.5,
};

test('cliff face is vertical at 90 degrees, sloping at 75, and overhanging at 15 degrees', () => {
  const vertical = g.dimensions(base);
  assert.equal(g.faceX(vertical, 70), 200);
  const slope = g.dimensions({ ...base, cliffSlope: 75 });
  const overhang = g.dimensions({ ...base, undercut: 15 });
  assert.ok(g.faceX(slope, 70) < 200);
  assert.ok(g.faceX(overhang, 70) > 200);
});

test('base remains solid and open domain remains empty', () => {
  const c = g.dimensions(base);
  assert.equal(g.materialContains(c, 200, 10), true);
  assert.equal(g.materialContains(c, 210, 60), false);
  assert.equal(g.materialContains(c, 150, 60), true);
});

test('rectangle reaches full width, ellipse and triangle taper toward notch edges', () => {
  const rectangle = g.dimensions(base);
  const ellipse = g.dimensions({ ...base, notchShape: 'ellipse' });
  const triangle = g.dimensions({ ...base, notchShape: 'triangle' });
  assert.equal(g.notchContains(rectangle, 173, 22), true);
  assert.equal(g.notchContains(ellipse, 173, 22), false);
  assert.equal(g.notchContains(triangle, 173, 22), false);
  assert.equal(g.notchContains(ellipse, 175, 30), true);
  assert.equal(g.notchContains(triangle, 175, 30), true);
});

test('triangle tip fraction changes the penetration profile', () => {
  const centreTip = g.dimensions({ ...base, notchShape: 'triangle' });
  const lowTip = g.dimensions({ ...base, notchShape: 'triangle', notchTipFraction: 0.25 });
  assert.equal(g.notchContains(centreTip, 175, 25), false);
  assert.equal(g.notchContains(lowTip, 175, 25), true);
});

test('zero height disables notches; a zero-depth setting uses legacy 1.5x height', () => {
  assert.equal(g.notchContains(g.dimensions({ ...base, notchHeight: 0 }), 180, 30), false);
  const automatic = g.dimensions({ ...base, notchDepth: 0 });
  assert.equal(g.notchContains(automatic, 175, 30), true);
  assert.equal(g.notchContains(automatic, 160, 30), false);
});

test('SVG preview is finite and distinguishes notch variants', () => {
  const a = g.previewMarkup({ ...base, notchShape: 'rectangle' });
  const b = g.previewMarkup({ ...base, notchShape: 'triangle' });
  assert.match(a, /GEOMETRY PREVIEW/);
  assert.notEqual(a, b);
  assert.equal(a.includes('NaN'), false);
  assert.equal(a.includes('Infinity'), false);
});
