'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const { EventEmitter } = require('node:events');
const childProcess = require('node:child_process');
const originalSpawn = childProcess.spawn;
const launches = [];
childProcess.spawn = (...args) => {
  const process = new EventEmitter();
  process.stdout = new EventEmitter();
  process.stderr = new EventEmitter();
  launches.push({ args, process });
  return process;
};
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-custom-enabled-'));
process.env.STUDIO_HOST = '127.0.0.1';
process.env.STUDIO_ALLOW_CUSTOM_LISP = '1';
process.env.STUDIO_OUTPUT_DIR = output;
const { server, CUSTOM_LISP_ENABLED } = require('../server.js');
test.before(async () => { await new Promise(resolve => server.listen(0, '127.0.0.1', resolve)); });
test.after(async () => {
  await new Promise(resolve => server.close(resolve));
  childProcess.spawn = originalSpawn;
  fs.rmSync(output, { recursive: true, force: true });
});
const base = () => 'http://127.0.0.1:' + server.address().port;
function request(payload, headers = {}) {
  return fetch(base() + '/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(payload) });
}
const source = '(in-package :cl-mpm-studio)\n;; trusted test source, never executed\n';

test('enabled API rejects missing confirmation, empty/oversized/NUL source before touching output', async () => {
  assert.equal(CUSTOM_LISP_ENABLED, true);
  for (const [payload, status] of [
    [{ constitutiveModel: 'custom', customModelSource: source }, 403],
    ...['', 'x'.repeat(32769), 'é'.repeat(16385), '(foo)\0'].map(customModelSource => [{ constitutiveModel: 'custom', confirmCustomExecution: true, customModelSource }, 400]),
    [null, 400], [[], 400],
  ]) assert.equal((await request(payload)).status, status);
  assert.equal(launches.length, 0);
  assert.equal(fs.existsSync(path.join(output, 'custom-model.lisp')), false);
});

test('loopback opt-in rejects a rebinding Host header and cross-site run/stop/video requests', async () => {
  // Fetch may replace Host; use raw HTTP to exercise the actual header received by Node.
  const status = await new Promise((resolve, reject) => {
    const req = http.request(base() + '/api/run', {
      method: 'POST', headers: { Host: 'attacker.example:' + server.address().port, 'Content-Type': 'application/json' },
    }, response => { response.resume(); response.on('end', () => resolve(response.statusCode)); });
    req.on('error', reject);
    req.end('{}');
  });
  assert.equal(status, 403);
  assert.equal((await request({}, { 'Sec-Fetch-Site': 'cross-site' })).status, 403);
  for (const pathname of ['/api/run', '/api/stop', '/api/make-video']) {
    const response = await fetch(base() + pathname, { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: 'https://other.example' }, body: '{}' });
    assert.equal(response.status, 403);
  }
  assert.equal(launches.length, 0);
});

test('oversized JSON receives an explicit 413 response', async () => {
  const response = await request({ padding: 'x'.repeat(65536) });
  assert.equal(response.status, 413);
  assert.match((await response.json()).error, /too large/);
});

test('custom source round trips exactly, concurrent runs are locked, and built-in runs never load it', async () => {
  const payload = { constitutiveModel: 'custom', confirmCustomExecution: true, customModelSource: source, cohesion: 0 };
  const responses = await Promise.all([request(payload), request(payload)]);
  assert.deepEqual(responses.map(r => r.status).sort(), [202, 409]);
  assert.equal(fs.readFileSync(path.join(output, 'custom-model.lisp'), 'utf8'), source);
  assert.equal(JSON.parse(fs.readFileSync(path.join(output, 'config.json'))).cohesion, 0);
  assert.equal(launches.length, 1);
  assert.match(launches[0].args[1].join(' '), /custom-model\.lisp/);
  launches[0].process.emit('close', 0);
  assert.equal((await request({ constitutiveModel: 'chalk' })).status, 202);
  assert.doesNotMatch(launches[1].args[1].join(' '), /custom-model\.lisp/);
  assert.equal(fs.existsSync(path.join(output, 'custom-model.lisp')), false);
  launches[1].process.emit('close', 0);
});
