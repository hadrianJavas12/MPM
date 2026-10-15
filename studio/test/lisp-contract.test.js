'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const workspace = require('../public/model-workspace.js');
const { normalize } = require('../public/config.js');
const schema = require('../schema.json').parameters;
const root = path.resolve(__dirname, '../..');
const sbcl = process.env.STUDIO_TEST_SBCL || 'sbcl';
const available = spawnSync(sbcl, ['--version'], { encoding: 'utf8' }).status === 0;
const required = process.env.STUDIO_REQUIRE_SBCL_TESTS === '1';

// These use a real SBCL reader/CLOS and production loader/config; matrix/JSON/runner
// dependencies are explicit stubs. They do not exercise the full MPM numerical engine.
function form(value) {
  if (value === null || value === false) return 'nil';
  if (value === true) return 't';
  if (typeof value === 'number') return String(value).replace(/e/i, 'd') + (String(value).includes('e') ? '' : 'd0');
  if (typeof value === 'string') return '"' + value.replace(/\\/g, '\\\\').replace(/"/g, '\\"') + '"';
  if (Array.isArray(value)) return '(list ' + value.map(form).join(' ') + ')';
  return '(let ((h (make-hash-table :test #\'equal))) ' + Object.entries(value).map(([k,v]) => '(setf (gethash ' + form(k) + ' h) ' + form(v) + ')').join(' ') + ' h)';
}
function runHarness(mode, input = {}) {
  assert.ok(available, 'Install SBCL or set STUDIO_TEST_SBCL; required SBCL tests cannot be skipped.');
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'studio lisp fixtures '));
  try {
    fs.mkdirSync(path.join(directory, 'registry/lisp'), { recursive: true });
    fs.writeFileSync(path.join(directory, 'registry/lisp/cl-mpm-studio.asd'), '(asdf:defsystem "cl-mpm-studio")');
    fs.copyFileSync(path.join(root, 'studio/schema.json'), path.join(directory, 'registry/schema.json'));
    const expected = normalize(input, schema);
    const entries = Object.entries(expected).map(([key, value]) => {
      const encoded = schema[key].type === 'enum' ? ':' + value : schema[key].type === 'integer' ? String(value) : form(value);
      return '(setf (gethash ' + form(key) + ' h) ' + encoded + ')';
    }).join('\n');
    fs.writeFileSync(path.join(directory, 'fixture.lisp'), '(setf jonathan::*schema-fixture* ' + form({parameters:schema}) + ')\n' +
      '(setf *input-config* ' + form(input) + ')\n' +
      '(setf *expected-config* (let ((h (make-hash-table :test #\'equal)))\n' + entries + '\nh))\n');
    const model = body => '(in-package :cl-mpm-studio)\n(defmethod cl-mpm/particle:constitutive-model ((mp studio-custom-chalk) strain dt) ' + body + ')\n';
    const fixtures = {
      'delegate.lisp': workspace.TEMPLATES.delegate, 'elastic.lisp': workspace.TEMPLATES.elastic,
      'custom-model.lisp': workspace.TEMPLATES.delegate,
      'missing.lisp': '(in-package :cl-mpm-studio)\n',
      'auxiliary.lisp': '(in-package :cl-mpm-studio)\n(defmethod cl-mpm/particle:constitutive-model :after ((mp studio-custom-chalk) strain dt) (values))',
      'wrong-signature.lisp': '(in-package :cl-mpm-studio)\n(defmethod cl-mpm/particle:constitutive-model ((mp studio-custom-chalk) strain) nil)',
      'partial.lisp': model('(call-next-method)') + '(error "partial load failed")',
      'invalid-stress.lisp': model('nil'),
      'wrong-shape.lisp': model('(make-instance \'magicl:matrix/double-float :shape \'(3 1))'),
      'infinite-stress.lisp': model('(make-instance \'magicl:matrix/double-float :storage (make-array 6 :element-type \'double-float :initial-element sb-ext:double-float-positive-infinity))'),
      'nan-stress.lisp': model('(make-instance \'magicl:matrix/double-float :storage (make-array 6 :element-type \'double-float :initial-element (sb-kernel:make-double-float #x7ff80000 0)))'),
      'simulation.lisp': workspace.exportRunScript(input),
    };
    for (const [name, contents] of Object.entries(fixtures)) fs.writeFileSync(path.join(directory, name), contents);
    const result = spawnSync(sbcl, ['--noinform', '--disable-debugger', '--script', path.join(__dirname, 'lisp-contract-harness.lisp'), root + path.sep, directory + path.sep, mode], {
      cwd: root, encoding: 'utf8', timeout: 30000, maxBuffer: 1024 * 1024,
    });
    assert.equal(result.status, 0, result.error?.message || (result.stdout + result.stderr).slice(0,3000));
    assert.match(result.stdout, /PASSED/);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
}
const options = { skip: !available && !required ? 'SBCL unavailable (CI requires it)' : false };
test('SBCL executes custom delegate/elastic methods and rejects missing, stale or invalid contracts', options, () => runHarness('model'));
test('SBCL reads and executes a custom export from a path with spaces using its adjacent model', options, () => runHarness('export', { constitutiveModel: 'custom', soilBoundary: 0, cohesion: 0, enableDamage: false, workers: 2.5, notchShape: 'ellipse' }));
test('SBCL exported built-in settings and production coercion match HTTP normalization', options, () => {
  const input = { E: '1e9', workers: 2.5, maxSteps: 99999, enableDamage: 'false', soilBoundary: 0, cohesion: 0, nu: 0.3 };
  runHarness('export', input);
  runHarness('config', input);
});
