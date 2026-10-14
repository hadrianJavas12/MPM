'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const api = require('../public/preset-modules.js');
const { normalize } = require('../public/config.js');
const schema = require('../schema.json').parameters;

const defaults = normalize({}, schema);

function moduleFile(id, lines) {
  return '(studio-module :version 1 :id :' + id + ')\n' +
    lines.join('\n') + '\n(end-module)\n';
}

test('single geometry module round-trips without changing material, solver or output', () => {
  const active = { ...defaults, soilBoundary: 0, cliffSlope: 75, E: 2e9, workers: 6 };
  const file = api.exportModules(['geometry'], active);
  const next = api.previewImport({ ...defaults, E: 3e9, workers: 8 }, '', file);
  assert.deepEqual(next.ids, ['geometry']);
  assert.equal(next.nextConfig.soilBoundary, 0);
  assert.equal(next.nextConfig.cliffSlope, 75);
  assert.equal(next.nextConfig.E, 3e9);
  assert.equal(next.nextConfig.workers, 8);
  assert.equal(next.nextConfig.plotMode, 'stress');
});

test('merge preserves omitted target fields while replace resets only this module', () => {
  const file = moduleFile('geometry', ['(param :soilBoundary 0d0)']);
  const initial = { ...defaults, soilBoundary: 80, cliffSlope: 55, E: 7e9 };
  const merged = api.previewImport(initial, '', file, 'merge');
  const replaced = api.previewImport(initial, '', file, 'replace');
  assert.equal(merged.nextConfig.cliffSlope, 55);
  assert.equal(replaced.nextConfig.cliffSlope, schema.cliffSlope.default);
  assert.equal(merged.nextConfig.soilBoundary, 0);
  assert.equal(replaced.nextConfig.soilBoundary, 0);
  assert.equal(replaced.nextConfig.E, 7e9);
  assert.equal(initial.soilBoundary, 80);
});

test('multiple modules are staged together, duplicates or conflicts fail atomically', () => {
  const selected = api.exportModules(['geometry', 'solver'], {
    ...defaults, shelfHeight: 120, workers: 3,
  });
  const plan = api.previewImport(defaults, '', selected);
  assert.deepEqual(plan.ids, ['geometry', 'solver']);
  assert.equal(plan.nextConfig.shelfHeight, 120);
  assert.equal(plan.nextConfig.workers, 3);
  assert.equal(plan.nextConfig.E, defaults.E);

  const invalid = selected.replace('(param :workers 3)', '(param :workers 999)');
  assert.throws(() => api.previewImport(defaults, '', invalid), /range/i);
  assert.equal(defaults.workers, 4);
  const duplicate = selected.replace('(end-preset)', moduleFile('geometry', ['(param :soilBoundary 0d0)']) + '(end-preset)');
  assert.throws(() => api.inspectImport(duplicate), /duplicate/i);
});

test('all settings + Unicode custom source round-trip through a complete preset', () => {
  const source = '(in-package :cl-mpm-studio)\n; kapur – α\n(defmethod example () (format t "hello"))';
  const original = { ...defaults, soilBoundary: 0, cohesion: 0,
    enableDamage: false, plotMode: 'velocity', workers: 3,
    constitutiveModel: 'custom' };
  const file = api.exportFullPreset(original, source);
  const inspection = api.inspectImport(file);
  assert.equal(inspection.complete, true);
  assert.deepEqual(new Set(inspection.ids), new Set(api.IDS));
  const next = api.previewImport(defaults, '', file, 'replace');
  assert.deepEqual(next.nextConfig, original);
  assert.equal(next.nextSource, source);
});

test('import never evaluates arbitrary Lisp or reader directives', () => {
  const hostile = [
    '#.(uiop:run-program "whoami")',
    "(load \"unexpected.lisp\")",
    "(studio-module :version 1 :id :geometry)\n(param :soilBoundary #.(print :bad))\n(end-module)",
    "(studio-module :version 1 :id :geometry)\n(param :E 2d0)\n(end-module)",
    "(studio-module :version 1 :id :geometry)\n(param :soilBoundary 2d0)\n(param :soilBoundary 3d0)\n(end-module)",
    "(studio-module :version 2 :id :geometry)\n(end-module)",
  ];
  hostile.forEach(src => assert.throws(() => api.inspectImport(src), undefined, src));
});

test('invalid enums, out-of-range numbers and missing custom source fail closed', () => {
  assert.throws(() => api.inspectImport(moduleFile('materials', ['(param :cohesion -1d0)'])), /range/i);
  assert.throws(() => api.inspectImport(moduleFile('output', ['(param :plotMode :unsafe)'])), /enum/i);
  assert.throws(() => api.previewImport(defaults, '',
    moduleFile('materials', ['(param :constitutiveModel :custom)'])), /requires source/i);
});

test('file size and custom source limits prevent oversized payloads', () => {
  assert.throws(() => api.inspectImport(' '.repeat(api.MAX_FILE_BYTES + 1)), /128 KiB/);
  assert.throws(() => api.exportModules(['constitutive-source'], defaults,
    'x'.repeat(api.MAX_SOURCE_BYTES + 1)), /32 KiB/);
});

test('malformed, trailing and incomplete file declarations cannot partly apply', () => {
  assert.throws(() => api.inspectImport('(studio-preset :version 1)\n(end-preset)'), /empty|invalid/i);
  assert.throws(() => api.inspectImport(moduleFile('output', ['(param :plotMode :stress)']) + '(print :bad)'), /trailing/i);
  assert.throws(() => api.previewImport(defaults, '', moduleFile('solver', ['(param :workers 4)']), 'invalid'), /merge or replace/);
});

test('full preset export refuses missing executable model source', () => {
  assert.throws(() => api.exportFullPreset({
    ...defaults, constitutiveModel: 'custom'
  }, ''), /requires nonempty constitutive source/i);
  assert.ok(api.exportModules(['geometry'], {
    ...defaults, constitutiveModel: 'custom'
  }, '').includes(':geometry'));
});
