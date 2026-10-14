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

// --- Paths & constants -------------------------------------------------------
const HOST = process.env.STUDIO_HOST || '127.0.0.1';
const PORT = Number(process.env.STUDIO_PORT || 3000);

const STUDIO_DIR = __dirname;
const ROOT = path.resolve(STUDIO_DIR, '..');
const PUBLIC_DIR = path.join(STUDIO_DIR, 'public');
const RUN_DIR = path.join(ROOT, 'output', 'studio');
const FRAMES_DIR = path.join(RUN_DIR, 'frames');
const VTK_DIR = path.join(RUN_DIR, 'vtk');
const VIDEO_PATH = path.join(RUN_DIR, 'video.mp4');
const CONFIG_PATH = path.join(RUN_DIR, 'config.json');
const LAUNCHER = path.join(ROOT, 'windows', 'cl-mpm.cmd');
const MAKE_VIDEO = path.join(ROOT, 'windows', 'make-video.cmd');
const RUNNER = path.join(STUDIO_DIR, 'lisp', 'run.lisp');

const SCHEMA = JSON.parse(fs.readFileSync(path.join(STUDIO_DIR, 'schema.json'), 'utf8')).parameters;
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
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(new Error('Request body too large'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try {
        const text = Buffer.concat(chunks).toString('utf8');
        resolve(text ? JSON.parse(text) : {});
      } catch {
        reject(new Error('Invalid JSON body'));
      }
    });
    req.on('error', reject);
  });
}

/** Coerce and clamp user input to the schema; unknown keys are dropped. */
function validateConfig(input) {
  const config = {};
  for (const [key, spec] of Object.entries(SCHEMA)) {
    const value = input[key];
    switch (spec.type) {
      case 'number':
      case 'integer': {
        let n = Number(value);
        if (value === undefined || value === null || value === '' || !Number.isFinite(n)) n = spec.default;
        n = Math.min(spec.max, Math.max(spec.min, n));
        config[key] = spec.type === 'integer' ? Math.round(n) : n;
        break;
      }
      case 'boolean':
        config[key] = value === undefined ? spec.default : value === true || value === 'true';
        break;
      case 'enum':
        config[key] = spec.values.includes(value) ? value : spec.default;
        break;
      default:
        config[key] = spec.default;
    }
  }
  return config;
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
  if (state.running) return sendJson(res, 409, { error: 'A simulation is already running.' });
  const config = validateConfig(await readJsonBody(req));

  await fsp.mkdir(RUN_DIR, { recursive: true });
  await Promise.all([emptyDir(FRAMES_DIR), emptyDir(VTK_DIR), fsp.rm(VIDEO_PATH, { force: true })]);
  await fsp.writeFile(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf8');

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

  child = spawnCmd(LAUNCHER, [RUNNER, CONFIG_PATH, RUN_DIR]);
  child.stdout.on('data', addLog);
  child.stderr.on('data', addLog);
  child.on('error', (err) => addLog(`[studio] Failed to start: ${err.message}`));
  child.on('close', (code) => {
    state.running = false;
    state.exitCode = code;
    child = null;
    if (stopRequested) {
      state.statusText = 'Aborted by user';
    } else if (code === 0) {
      state.percent = 100;
      state.statusText = 'Finished';
      addLog('[studio] Simulation finished.');
    } else {
      state.statusText = `Failed (exit code ${code})`;
      addLog(`[studio] Runner exited with code ${code}.`);
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
  if (videoBusy) return sendJson(res, 409, { error: 'A video is already being rendered.' });
  const body = await readJsonBody(req);
  const fps = Math.min(60, Math.max(1, Math.round(Number(body.fps) || 15)));
  const frames = (await listDir(FRAMES_DIR)).filter((f) => FRAME_RE.test(f));
  if (frames.length === 0) return sendJson(res, 400, { error: 'No frames to encode. Run a simulation first.' });

  videoBusy = true;
  addLog(`[studio] Encoding ${frames.length} frames at ${fps} fps...`);
  const proc = spawnCmd(MAKE_VIDEO, [FRAMES_DIR, String(fps), VIDEO_PATH]);
  let output = '';
  proc.stdout.on('data', (d) => (output += d));
  proc.stderr.on('data', (d) => (output += d));
  proc.on('close', (code) => {
    videoBusy = false;
    const tail = output.trim().split(/\r?\n/).slice(-5).join('\n');
    if (code === 0) {
      addLog('[studio] Video ready: output/studio/video.mp4');
      sendJson(res, 200, { ok: true, videoUrl: '/api/video' });
    } else {
      addLog(`[studio] Video encoding failed (exit ${code}).`);
      addLog(tail);
      sendJson(res, 500, { error: `ffmpeg failed (exit ${code})`, output: tail });
    }
  });
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
  const { pathname, searchParams } = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const method = req.method;

  if (method === 'GET' && pathname === '/api/status') return sendJson(res, 200, state);
  if (method === 'GET' && pathname === '/api/schema') return sendJson(res, 200, SCHEMA);
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
  if (method === 'POST' && pathname === '/api/stop') return stopRun(res);
  if (method === 'POST' && pathname === '/api/make-video') return makeVideo(req, res);
  if (pathname.startsWith('/api/')) return sendJson(res, 404, { error: 'Unknown endpoint' });
  if (method === 'GET' || method === 'HEAD') return serveStatic(req, res, pathname);
  res.writeHead(405);
  res.end();
}

const server = http.createServer((req, res) => {
  route(req, res).catch((err) => {
    if (!res.headersSent) sendJson(res, 400, { error: err.message });
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

server.listen(PORT, HOST, () => {
  console.log('CL-MPM Studio');
  console.log(`  UI:      http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
  console.log(`  Output:  ${RUN_DIR}`);
  console.log('Press Ctrl+C to stop.');
});
