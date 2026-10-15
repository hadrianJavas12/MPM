'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'cl-mpm-studio-test-'));
process.env.STUDIO_OUTPUT_DIR = temp;
const { server, validateConfig } = require('../server.js');

test.after(() => {
  server.close();
  fs.rmSync(temp, { recursive: true, force: true });
});

test('validation preserves zero and clamps values within schema bounds', () => {
  const config = validateConfig({ soilBoundary: 0, maxSteps: 99999, workers: -10, plotMode: 'unknown' });
  assert.equal(config.soilBoundary, 0);
  assert.equal(config.maxSteps, 2000);
  assert.equal(config.workers, 1);
  assert.equal(config.plotMode, 'stress');
  assert.equal(config.delayTime, 10);
  assert.equal(Object.prototype.hasOwnProperty.call(config, 'unexpected'), false);
});

test('validation ignores invalid values and unknown keys', () => {
  const config = validateConfig({ shelfHeight: 'n/a', E: 'NaN', enableDamage: false, unknownKey: 20 });
  assert.equal(config.shelfHeight, 100);
  assert.equal(config.E, 1e9);
  assert.equal(config.enableDamage, false);
  assert.equal('unknownKey' in config, false);
});

test('API returns 400 if encoding is requested without frames', async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  const result = await fetch(`http://127.0.0.1:${port}/api/make-video`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fps: 15 }),
  });
  assert.equal(result.status, 400);
  assert.match((await result.json()).error, /No frames/);
});

test('GET status and schema work without SBCL', async () => {
  const base = `http://127.0.0.1:${server.address().port}`;
  const [status, schema] = await Promise.all([fetch(base + '/api/status'), fetch(base + '/api/schema')]);
  assert.equal(status.status, 200);
  assert.equal((await status.json()).running, false);
  assert.equal(schema.status, 200);
  assert.equal((await schema.json()).soilBoundary.min, 0);
});
