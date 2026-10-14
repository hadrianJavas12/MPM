'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const workspace = require('../public/model-workspace.js');

test('custom templates target the dedicated Studio particle subclass', () => {
  for (const source of Object.values(workspace.TEMPLATES)) {
    assert.match(source, /studio-custom-chalk/);
    assert.match(source, /constitutive-model/);
    assert.equal(workspace.validateSource(source).ok, true);
  }
});

test('source checker ignores strings and comments, but checks parentheses', () => {
  assert.equal(workspace.validateSource('(list "quoted )" 1) ; ignored (\n').ok, true);
  assert.equal(workspace.validateSource('#| ( nested #| ) |# ) |# (foo)').ok, true);
  assert.equal(workspace.validateSource('(foo (bar)').ok, false);
  assert.equal(workspace.validateSource('foo)').ok, false);
  assert.equal(workspace.validateSource('(foo "incomplete)').ok, false);
});

test('script input is bounded and cannot contain NUL', () => {
  assert.equal(workspace.validateSource(' ').ok, false);
  assert.equal(workspace.validateSource('x'.repeat(workspace.MAX_SOURCE_BYTES + 1)).ok, false);
  assert.equal(workspace.validateSource('(x)\0').ok, false);
});

test('simulation exporter encodes numbers, booleans, allowed keywords and custom load', () => {
  const script = workspace.exportRunScript({
    E: 1e9, soilBoundary: 0, enableDamage: false,
    workers: 4, notchShape: 'ellipse', plotMode: 'stress',
    constitutiveModel: 'custom',
  });
  assert.match(script, /\(gethash "E" config\) 1000000000d0/);
  assert.match(script, /\(gethash "soilBoundary" config\) 0d0/);
  assert.match(script, /\(gethash "enableDamage" config\) nil/);
  assert.match(script, /\(gethash "workers" config\) 4/);
  assert.match(script, /\(gethash "constitutiveModel" config\) :custom/);
  assert.match(script, /load \(merge-pathnames "custom-model.lisp"/);
  assert.doesNotMatch(script, /undefined|NaN|Infinity/);
});

test('unsafe export values fail closed; unknown keys are ignored', () => {
  assert.throws(() => workspace.exportRunScript({ constitutiveModel: '"; (delete-files)' }));
  assert.throws(() => workspace.exportRunScript({ cohesion: Infinity }));
  assert.doesNotMatch(workspace.exportRunScript({ arbitraryKey: 'unsafe' }), /arbitraryKey/);
});
