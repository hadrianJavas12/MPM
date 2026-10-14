'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

process.env.STUDIO_ALLOW_CUSTOM_LISP = '0';
const output = fs.mkdtempSync(path.join(os.tmpdir(), 'studio-custom-guard-'));
process.env.STUDIO_OUTPUT_DIR = output;
const { server, CUSTOM_LISP_ENABLED } = require('../server.js');

test.before(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
});
test.after(async () => {
  await new Promise(resolve => server.close(resolve));
  fs.rmSync(output, { recursive: true, force: true });
});

function endpoint(pathname) {
  return 'http://127.0.0.1:' + server.address().port + pathname;
}

test('custom execution disabled by default while editor and export remain usable', async () => {
  assert.equal(CUSTOM_LISP_ENABLED, false);
  const result = await fetch(endpoint('/api/custom-model-capabilities'));
  assert.equal(result.status, 200);
  const body = await result.json();
  assert.equal(body.enabled, false);
  assert.match(body.warning, /no sandbox/i);
});

test('custom code is rejected without explicit local server opt-in', async () => {
  const request = await fetch(endpoint('/api/run'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      constitutiveModel: 'custom',
      customModelSource: '(error "not approved")',
      confirmCustomExecution: true,
    }),
  });
  assert.equal(request.status, 403);
  assert.match((await request.json()).error, /disabled/i);
  assert.equal(fs.existsSync(path.join(output, 'custom-model.lisp')), false);
});

test('cross-origin request is rejected before processing', async () => {
  const request = await fetch(endpoint('/api/run'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Origin: 'https://untrusted.example' },
    body: '{}',
  });
  assert.equal(request.status, 403);
});

test('non-JSON requests cannot invoke the runner', async () => {
  const request = await fetch(endpoint('/api/run'), {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: '{}',
  });
  assert.equal(request.status, 415);
});
