'use strict';
/**
 * CL-MPM Studio server.
 *
 * Zero-dependency Node.js (>= 18) HTTP server that
 *   - serves the browser UI from ./public,
 *   - validates run parameters against ./schema.json,
 *   - launches the Lisp runner (studio/lisp/run.lisp) through windows\cl-mpm.cmd,
 *   - exposes progress, logs, PNG frames, VTK files and the MP4 video.
 *
 * All paths are derived from this file's location; nothing is user specific.
 * Environment overrides: STUDIO_HOST (default 127.0.0.1), STUDIO_PORT (3000).
 */
const http = require('node:http');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const { spawn } = require('node:child_process');
const { normalize } = require('./public/config.js');

// --- Paths & constants -------------------------------------------------------
const HOST = process.env.STUDIO_HOST || '127.0.0.1';
const PORT = Number(process.env.STUDIO_PORT || 3000);

const STUDIO_DIR = __dirname;
const ROOT = path.resolve(STUDIO_DIR, '..');
const PUBLIC_DIR = path.join(STUDIO_DIR, 'public');
const RUN_DIR = path.resolve(process.env.STUDIO_OUTPUT_DIR || path.join(ROOT, 'output', 'studio'));
const FRAMES_DIR = path.join(RUN_DIR, 'frames');
const VTK_DIR = path.join(RUN_DIR, 'vtk');
const VIDEO_PATH = path.join(RUN_DIR, 'video.mp4');
const CONFIG_PATH = path.join(RUN_DIR, 'config.json');
const CUSTOM_MODEL_PATH = path.join(RUN_DIR, 'custom-model.lisp');
// Arbitrary Lisp has OS-level privileges. NEVER enable on a remote server.
const CUSTOM_LISP_ENABLED =
  process.env.STUDIO_ALLOW_CUSTOM_LISP === '1' &&
  ['127.0.0.1', 'localhost', '::1'].includes(HOST);
const MAX_CUSTOM_SOURCE_BYTES = 32 * 1024;
const LAUNCHER = path.join(ROOT, 'windows', 'cl-mpm.cmd');
const MAKE_VIDEO = path.join(ROOT, 'windows', 'make-video.cmd');
const RUNNER = path.join(STUDIO_DIR, 'lisp', 'run.lisp');

const SCHEMA = JSON.parse(fs.readFileSync(path.join(STUDIO_DIR, 'schema.json'), 'utf8')).parameters;
const REFERENCE_PRESETS = JSON.parse(fs.readFileSync(path.join(STUDIO_DIR, 'reference-presets.json'), 'utf8'));
const MAX_LOG_LINES = 2000;
const MAX_BODY_BYTES = 64 * 1024;
const FRAME_RE = /^frame_\d{5}\.png$/;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

// --- State -------------------------------------------------------------------
const state = {
  running: false,
  step: 0,
  totalSteps: 0,
  percent: 0,
  statusText: 'Engine idle',
  startTime: null,
  exitCode: null,
};
let child = null;
let stopRequested = false;
let videoBusy = false;

/** Ring buffer of log lines; `firstSeq` is the sequence number of lines[0]. */
const logBuffer = { lines: [], firstSeq: 0 };

function addLog(text) {
  for (const raw of String(text).split(/\r?\n/)) {
    const line = raw.trimEnd();
    if (!line) continue;
    logBuffer.lines.push(line);
    const m = line.match(/^Step\s+(\d+)\/(\d+)/);
    if (m) {
      state.step = Number(m[1]);
      state.totalSteps = Number(m[2]);
      state.percent = Math.round((100 * state.step) / Math.max(1, state.totalSteps));
      state.statusText = `Simulating step ${state.step}/${state.totalSteps}`;
    }
  }
  const excess = logBuffer.lines.length - MAX_LOG_LINES;
  if (excess > 0) {
    logBuffer.lines.splice(0, excess);
    logBuffer.firstSeq += excess;
  }
}

// --- Helpers -----------------------------------------------------------------
function sendJson(res, status, body) {
  res.writeHead(status, { 'Content-Type': MIME['.json'], 'Cache-Control': 'no-store' });
  res.end(JSON.stringify(body));
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    let tooLarge = false;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (tooLarge) return;
      if (size > MAX_BODY_BYTES) {
        tooLarge = true;
        chunks.length = 0;
        reject(Object.assign(new Error('Request body too large'), { statusCode: 413 }));
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (tooLarge) return;
      try {
        const text = Buffer.concat(chunks).toString('utf8');
        const value = text ? JSON.parse(text) : {};
        if (!value || typeof value !== 'object' || Array.isArray(value))
          throw new TypeError('JSON object required');
        resolve(value);
      } catch {
        reject(new Error('Request body must be a valid JSON object.'));
      }
    });
    req.on('error', reject);
  });
}

/** Coerce and clamp user input to the schema; unknown keys are dropped. */
function validateConfig(input) {
  return normalize(input, SCHEMA);
}

function guardMutation(req, res, jsonRequired = true) {
  const expectedOrigin = `http://${req.headers.host}`;
  if ((req.headers.origin && req.headers.origin !== expectedOrigin) ||
      req.headers['sec-fetch-site'] === 'cross-site') {
    sendJson(res, 403, { error: 'Cross-origin simulation requests are not permitted.' });
    return false;
  }
  if (jsonRequired && !/^application\/json(?:\s*;|\s*$)/i.test(req.headers['content-type'] || '')) {
    sendJson(res, 415, { error: 'Content-Type must be application/json.' });
    return false;
  }
  return true;
}

/** Run a .cmd file through cmd.exe with correctly quoted arguments. */
function spawnCmd(script, args) {
  const line = [script, ...args].map((a) => `"${a}"`).join(' ');
  return spawn('cmd.exe', ['/d', '/s', '/c', `"${line}"`], {
    cwd: ROOT,
    windowsVerbatimArguments: true,
    windowsHide: true,
  });
}

async function emptyDir(dir) {
  await fsp.rm(dir, { recursive: true, force: true });
  await fsp.mkdir(dir, { recursive: true });
}

async function listDir(dir) {
  try {
    return await fsp.readdir(dir);
  } catch {
    return [];
  }
}

function streamFile(req, res, filePath, contentType) {
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not found');
      return;
    }
    const range = req.headers.range && req.headers.range.match(/bytes=(\d*)-(\d*)/);
    if (range && (range[1] || range[2])) {
      const start = range[1] ? Number(range[1]) : Math.max(0, stat.size - Number(range[2]));
      const end = range[1] && range[2] ? Math.min(Number(range[2]), stat.size - 1) : stat.size - 1;
      if (start > end || start >= stat.size) {
        res.writeHead(416, { 'Content-Range': `bytes */${stat.size}` });
        res.end();
        return;
      }
      res.writeHead(206, {
        'Content-Type': contentType,
        'Content-Range': `bytes ${start}-${end}/${stat.size}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': end - start + 1,
        'Cache-Control': 'no-store',
      });
      fs.createReadStream(filePath, { start, end }).pipe(res);
      return;
    }
    res.writeHead(200, {
      'Content-Type': contentType,
      'Content-Length': stat.size,
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'no-store',
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

// --- API handlers ------------------------------------------------------------
async function startRun(req, res) {
  // Reject browser cross-origin requests and non-JSON forms before parsing.
  if (!guardMutation(req, res)) return;
  if (state.running) return sendJson(res, 409, { error: 'A simulation is already running.' });
  const payload = await readJsonBody(req);
  // Check again AFTER reading the body: two requests may have awaited it together.
  if (state.running) return sendJson(res, 409, { error: 'A simulation is already running.' });
  if (videoBusy) return sendJson(res, 409, { error: 'Wait for video encoding to finish.' });
  const config = validateConfig(payload);
  if (config.scenario === 'joss-bay' && config.constitutiveModel === 'custom') {
    return sendJson(res, 400, { error: 'Joss Bay uses its dedicated reference material. Select the built-in model for this scenario.' });
  }
  const isCustom = config.constitutiveModel === 'custom';
  let customSource = null;
  if (isCustom) {
    if (!CUSTOM_LISP_ENABLED) return sendJson(res, 403, {
      error: 'Custom Lisp execution is disabled. Run Studio on loopback with STUDIO_ALLOW_CUSTOM_LISP=1 to opt in.',
    });
    if (payload.confirmCustomExecution !== true) return sendJson(res, 403, {
      error: 'Explicit confirmation is required to execute user Lisp.',
    });
    if (typeof payload.customModelSource !== 'string' || !payload.customModelSource.trim() ||
        payload.customModelSource.includes('\0') ||
        Buffer.byteLength(payload.customModelSource, 'utf8') > MAX_CUSTOM_SOURCE_BYTES) {
      return sendJson(res, 400, { error: 'Supply a nonempty .lisp source of at most 32 KiB without NUL bytes.' });
    }
    customSource = payload.customModelSource;
  }

  // Acquire the run lock before the first filesystem await.
  Object.assign(state, {
    running: true,
    step: 0,
    totalSteps: config.maxSteps,
    percent: 0,
    statusText: 'Starting SBCL...',
    startTime: Date.now(),
    exitCode: null,
  });
  logBuffer.lines = [];
  logBuffer.firstSeq = 0;
  stopRequested = false;
  addLog(`[studio] Launching: ${config.maxSteps} frames x ${config.substeps} steps, h=${config.meshSize} m, colour=${config.plotMode}`);

  try {
    await fsp.mkdir(RUN_DIR, { recursive: true });
    await Promise.all([
      emptyDir(FRAMES_DIR),
      emptyDir(VTK_DIR),
      fsp.rm(VIDEO_PATH, { force: true }),
      fsp.rm(CUSTOM_MODEL_PATH, { force: true }),
    ]);
    await fsp.writeFile(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');
    if (isCustom) await fsp.writeFile(CUSTOM_MODEL_PATH, customSource, { mode: 0o600 });
    child = spawnCmd(LAUNCHER, [
      RUNNER, CONFIG_PATH, RUN_DIR, ...(isCustom ? [CUSTOM_MODEL_PATH] : []),
    ]);
  } catch (err) {
    state.running = false;
    state.exitCode = -1;
    state.statusText = `Failed to launch: ${err.message}`;
    addLog(`[studio] ${state.statusText}`);
    throw err;
  }
  child.stdout.on('data', addLog);
  child.stderr.on('data', addLog);
  let runnerError = null;
  child.on('error', (err) => {
    runnerError = err;
    addLog(`[studio] Failed to start: ${err.message}`);
  });
  child.on('close', (code) => {
    state.running = false;
    state.exitCode = runnerError ? -1 : code;
    child = null;
    if (stopRequested) {
      state.statusText = 'Aborted by user';
    } else if (code === 0 && !runnerError) {
      state.percent = 100;
      state.statusText = 'Finished';
      addLog('[studio] Simulation finished.');
    } else {
      state.statusText = runnerError ? `Failed to start: ${runnerError.message}` : `Failed (exit code ${code})`;
      addLog(`[studio] ${state.statusText}`);
    }
  });
  sendJson(res, 202, { ok: true, config });
}

function stopRun(res) {
  if (!child) return sendJson(res, 200, { ok: true, message: 'No simulation running.' });
  stopRequested = true;
  spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
  addLog('[studio] Stop requested.');
  sendJson(res, 200, { ok: true, message: 'Stopping simulation.' });
}

async function makeVideo(req, res) {
  if (!guardMutation(req, res)) return;
  const body = await readJsonBody(req);
  if (state.running) return sendJson(res, 409, { error: 'Wait for the simulation to finish.' });
  if (videoBusy) return sendJson(res, 409, { error: 'A video is already being rendered.' });

  // Lock before reading the filesystem; a new run must not clear these frames.
  videoBusy = true;
  try {
    const fps = Math.min(60, Math.max(1, Math.round(Number(body.fps) || 15)));
    const frames = (await listDir(FRAMES_DIR)).filter((f) => FRAME_RE.test(f));
    if (frames.length === 0) {
      videoBusy = false;
      return sendJson(res, 400, { error: 'No frames to encode. Run a simulation first.' });
    }

    addLog(`[studio] Encoding ${frames.length} frames at ${fps} fps...`);
    const proc = spawnCmd(MAKE_VIDEO, [FRAMES_DIR, String(fps), VIDEO_PATH]);
    let output = '';
    let finished = false;
    proc.stdout.on('data', (d) => (output += d));
    proc.stderr.on('data', (d) => (output += d));
    const finish = (code, err) => {
      if (finished) return; // spawn errors may be followed by a close event.
      finished = true;
      videoBusy = false;
      const tail = output.trim().split(/\r?\n/).slice(-5).join('\n');
      if (err) {
        addLog(`[studio] Video encoder could not start: ${err.message}`);
        return sendJson(res, 500, { error: `Video encoder could not start: ${err.message}` });
      }
      if (code === 0) {
        addLog('[studio] Video ready: output/studio/video.mp4');
        return sendJson(res, 200, { ok: true, videoUrl: '/api/video' });
      }
      addLog(`[studio] Video encoding failed (exit ${code}).`);
      addLog(tail);
      return sendJson(res, 500, { error: `ffmpeg failed (exit ${code})`, output: tail });
    };
    proc.on('error', (err) => finish(-1, err));
    proc.on('close', (code) => finish(code, null));
  } catch (err) {
    videoBusy = false;
    throw err;
  }
}

async function listFrames(res) {
  const frames = (await listDir(FRAMES_DIR)).filter((f) => FRAME_RE.test(f)).sort();
  sendJson(res, 200, { frames });
}

async function listVtk(res) {
  const names = (await listDir(VTK_DIR)).filter((f) => f.endsWith('.vtk'));
  const files = await Promise.all(
    names.map(async (name) => {
      const st = await fsp.stat(path.join(VTK_DIR, name));
      return { name, sizeBytes: st.size, modified: st.mtime };
    }),
  );
  files.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
  sendJson(res, 200, { directory: path.relative(ROOT, VTK_DIR), files });
}

function serveStatic(req, res, pathname) {
  let rel;
  try {
    rel = decodeURIComponent(pathname === '/' ? '/index.html' : pathname);
  } catch {
    res.writeHead(400);
    return res.end('Bad request');
  }
  const filePath = path.resolve(PUBLIC_DIR, '.' + rel);
  if (!filePath.startsWith(PUBLIC_DIR + path.sep)) {
    res.writeHead(403);
    return res.end('Forbidden');
  }
  streamFile(req, res, filePath, MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream');
}

// --- Router ------------------------------------------------------------------
async function route(req, res) {
  if (CUSTOM_LISP_ENABLED) {
    // Binding localhost alone does not reject a request addressed to a rebinding domain.
    const authority = new URL(`http://${req.headers.host || ''}`);
    if (!['127.0.0.1', 'localhost', '[::1]'].includes(authority.hostname) ||
        authority.username || authority.password || authority.pathname !== '/' ||
        Number(authority.port || 80) !== server.address().port)
      return sendJson(res, 403, { error: 'Custom Lisp requires a loopback Host header and the Studio port.' });
  }
  const { pathname, searchParams } = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const method = req.method;

  if (method === 'GET' && pathname === '/api/status') return sendJson(res, 200, state);
  if (method === 'GET' && pathname === '/api/schema') return sendJson(res, 200, SCHEMA);
  if (method === 'GET' && pathname === '/api/reference-presets') return sendJson(res, 200, REFERENCE_PRESETS);
  if (method === 'GET' && pathname === '/api/custom-model-capabilities')
    return sendJson(res, 200, {
      enabled: CUSTOM_LISP_ENABLED,
      maxSourceBytes: MAX_CUSTOM_SOURCE_BYTES,
      warning: 'Lisp code is executed with the local user privileges; no sandbox is provided.',
    });
  if (method === 'GET' && pathname === '/api/logs') {
    const since = Math.max(logBuffer.firstSeq, Number(searchParams.get('since')) || 0);
    const lines = logBuffer.lines.slice(since - logBuffer.firstSeq);
    return sendJson(res, 200, { lines, next: logBuffer.firstSeq + logBuffer.lines.length });
  }
  if (method === 'GET' && pathname === '/api/frames') return listFrames(res);
  if (method === 'GET' && pathname.startsWith('/api/frame/')) {
    const name = pathname.slice('/api/frame/'.length);
    if (!FRAME_RE.test(name)) return sendJson(res, 400, { error: 'Invalid frame name' });
    return streamFile(req, res, path.join(FRAMES_DIR, name), MIME['.png']);
  }
  if (method === 'GET' && pathname === '/api/output-files') return listVtk(res);
  if (method === 'GET' && pathname === '/api/video') return streamFile(req, res, VIDEO_PATH, 'video/mp4');
  if (method === 'POST' && pathname === '/api/run') return startRun(req, res);
  if (method === 'POST' && pathname === '/api/stop') {
    if (!guardMutation(req, res, false)) return;
    return stopRun(res);
  }
  if (method === 'POST' && pathname === '/api/make-video') return makeVideo(req, res);
  if (pathname.startsWith('/api/')) return sendJson(res, 404, { error: 'Unknown endpoint' });
  if (method === 'GET' || method === 'HEAD') return serveStatic(req, res, pathname);
  res.writeHead(405);
  res.end();
}

const server = http.createServer((req, res) => {
  route(req, res).catch((err) => {
    if (!res.headersSent) sendJson(res, err.statusCode || 400, { error: err.message });
    else res.end();
  });
});

function shutdown() {
  if (child) spawn('taskkill', ['/pid', String(child.pid), '/t', '/f'], { windowsHide: true });
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 2000).unref();
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

if (require.main === module) {
  server.listen(PORT, HOST, () => {
    console.log('CL-MPM Studio');
    console.log(`  UI:      http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
    console.log(`  Output:  ${RUN_DIR}`);
    console.log('Press Ctrl+C to stop.');
  });
}

// Export the server without binding a port, allowing dependency-free API tests.
module.exports = { server, validateConfig, CUSTOM_LISP_ENABLED };
