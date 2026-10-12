const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');

const PORT = 3000;
const WORKSPACE = __dirname;
const OUT_FRAMES_DIR = path.join(WORKSPACE, 'outframes');
const OUTPUT_DIR = path.join(WORKSPACE, 'output');
const VIDEO_PATH = path.join(WORKSPACE, 'simulation_video.mp4');
const UI_DIR = path.join(WORKSPACE, 'web_ui');

let currentProcess = null;
let simulationState = {
  running: false,
  step: 0,
  totalSteps: 0,
  percent: 0,
  statusText: 'Engine Idle',
  startTime: null,
  logs: []
};

function addLog(msg) {
  const line = msg.toString();
  simulationState.logs.push(line);
  if (simulationState.logs.length > 500) {
    simulationState.logs.shift();
  }
  // Detect step progress
  const stepMatch = line.match(/Step\s+(\d+)\/(\d+)/i);
  if (stepMatch) {
    simulationState.step = parseInt(stepMatch[1]);
    simulationState.totalSteps = parseInt(stepMatch[2]);
    simulationState.percent = Math.round((simulationState.step / simulationState.totalSteps) * 100);
    simulationState.statusText = `Simulating Step ${simulationState.step}/${simulationState.totalSteps}`;
  }
}

// Ensure directories
if (!fs.existsSync(OUT_FRAMES_DIR)) fs.mkdirSync(OUT_FRAMES_DIR, { recursive: true });
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });
if (!fs.existsSync(UI_DIR)) fs.mkdirSync(UI_DIR, { recursive: true });

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = parsedUrl.pathname;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // --- API: Status ---
  if (pathname === '/api/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(simulationState));
    return;
  }

  // --- API: Logs ---
  if (pathname === '/api/logs' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ logs: simulationState.logs }));
    return;
  }

  // --- API: Frames List ---
  if (pathname === '/api/frames' && req.method === 'GET') {
    fs.readdir(OUT_FRAMES_DIR, (err, files) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      const pngs = (files || [])
        .filter(f => f.toLowerCase().endsWith('.png'))
        .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ frames: pngs }));
    });
    return;
  }

  // --- API: Frame Image ---
  if (pathname.startsWith('/api/frame/') && req.method === 'GET') {
    const frameName = path.basename(pathname.replace('/api/frame/', ''));
    const filePath = path.join(OUT_FRAMES_DIR, frameName);
    if (fs.existsSync(filePath)) {
      res.writeHead(200, { 'Content-Type': 'image/png' });
      fs.createReadStream(filePath).pipe(res);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Frame not found');
    }
    return;
  }

  // --- API: Video Stream ---
  if (pathname === '/api/video' && req.method === 'GET') {
    if (!fs.existsSync(VIDEO_PATH)) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Video not found. Generate it first using Make Video.');
      return;
    }
    const stat = fs.statSync(VIDEO_PATH);
    const fileSize = stat.size;
    const range = req.headers.range;

    if (range) {
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      const file = fs.createReadStream(VIDEO_PATH, { start, end });
      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
      });
      file.pipe(res);
    } else {
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
      });
      fs.createReadStream(VIDEO_PATH).pipe(res);
    }
    return;
  }

  // --- API: Output Files List (VTK) ---
  if (pathname === '/api/output-files' && req.method === 'GET') {
    fs.readdir(OUTPUT_DIR, (err, files) => {
      if (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
        return;
      }
      const fileList = (files || []).map(f => {
        try {
          const st = fs.statSync(path.join(OUTPUT_DIR, f));
          return { name: f, sizeBytes: st.size, modified: st.mtime };
        } catch(e) {
          return { name: f, sizeBytes: 0, modified: new Date() };
        }
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ files: fileList }));
    });
    return;
  }

  // --- API: Run Simulation ---
  if (pathname === '/api/run' && req.method === 'POST') {
    if (simulationState.running) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Simulation is already running!' }));
      return;
    }

    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const config = JSON.parse(body || '{}');

        // Clean outframes if clean requested
        if (config.clearFrames) {
          try {
            const old = fs.readdirSync(OUT_FRAMES_DIR);
            old.forEach(f => {
              if (f.endsWith('.png')) fs.unlinkSync(path.join(OUT_FRAMES_DIR, f));
            });
          } catch(e) {}
        }

        // Generate simulation_config.lisp
        const lispConfig = `;;; Automatically generated by CL-MPM Studio Web UI
(in-package :cl-user)
(defparameter *ui-shelf-height* ${parseFloat(config.shelfHeight || 100)}d0)
(defparameter *ui-shelf-aspect* ${parseFloat(config.shelfAspect || 2.0)}d0)
(defparameter *ui-soil-boundary* ${parseFloat(config.soilBoundary || 20)}d0)
(defparameter *ui-mesh-size* ${parseFloat(config.meshSize || 5)}d0)
(defparameter *ui-mps-per-cell* ${parseInt(config.mpsPerCell || 2)})
(defparameter *ui-undercut* ${parseFloat(config.undercut || 0)}d0)
(defparameter *ui-density* ${parseFloat(config.density || 1700)}d0)
(defparameter *ui-E* ${parseFloat(config.E || 1e9)}d0)
(defparameter *ui-nu* ${parseFloat(config.nu || 0.35)}d0)
(defparameter *ui-friction-angle* ${parseFloat(config.frictionAngle || 40)}d0)
(defparameter *ui-fracture-energy* ${parseFloat(config.fractureEnergy || 3000)}d0)
(defparameter *ui-initiation-stress* ${parseFloat(config.initiationStress || 200e3)}d0)
(defparameter *ui-delay-time* ${parseFloat(config.delayTime || 10)}d0)
(defparameter *ui-max-steps* ${parseInt(config.maxSteps || 10)})
(defparameter *ui-substeps* ${parseInt(config.substeps || 10)})
(defparameter *ui-plot-mode* :${config.plotMode || 'stress'})
(defparameter *ui-workers* ${parseInt(config.workers || 4)})
(defparameter *ui-enable-damage* ${config.enableDamage !== false ? 't' : 'nil'})
`;
        fs.writeFileSync(path.join(WORKSPACE, 'simulation_config.lisp'), lispConfig, 'utf8');

        // Reset state
        simulationState.running = true;
        simulationState.step = 0;
        simulationState.totalSteps = parseInt(config.maxSteps || 10);
        simulationState.percent = 0;
        simulationState.statusText = 'Starting SBCL Engine...';
        simulationState.startTime = Date.now();
        simulationState.logs = [];

        addLog(`[UI] Launching simulation: ${simulationState.totalSteps} steps, mesh ${config.meshSize}m, mode ${config.plotMode}`);

        // Set up environment with SBCL, MinGW, OpenBLAS, Gnuplot
        const env = { ...process.env };
        const MINGW_DIR = "C:\\Users\\ASUS\\AppData\\Local\\Microsoft\\WinGet\\Packages\\BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\\mingw64\\bin";
        const GNUPLOT_DIR = "C:\\Users\\ASUS\\AppData\\Local\\Microsoft\\WinGet\\Packages\\gnuplot.gnuplot_Microsoft.Winget.Source_8wekyb3d8bbwe\\gnuplot\\bin";
        env.PATH = `C:\\Program Files\\Steel Bank Common Lisp;${MINGW_DIR};D:\\MPM\\openblas\\bin;${GNUPLOT_DIR};D:\\MPM\\libs;D:\\MPM;${env.PATH || ''}`;

        const sbclArgs = [
          '--dynamic-space-size', '4000',
          '--disable-debugger',
          '--no-userinit',
          '--load', 'D:\\MPM\\init.lisp',
          '--load', 'D:\\MPM\\simulation_config.lisp',
          '--load', 'D:\\MPM\\run_ui_runner.lisp'
        ];

        currentProcess = spawn('sbcl.exe', sbclArgs, { cwd: WORKSPACE, env });

        currentProcess.stdout.on('data', data => addLog(data));
        currentProcess.stderr.on('data', data => addLog(data));

        currentProcess.on('close', code => {
          simulationState.running = false;
          currentProcess = null;
          if (code === 0) {
            simulationState.percent = 100;
            simulationState.statusText = 'Simulation Finished Successfully';
            addLog('[UI] Simulation run completed successfully!');
          } else {
            simulationState.statusText = `Simulation Terminated (Exit code ${code})`;
            addLog(`[UI] Process terminated with exit code ${code}`);
          }
        });

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true, message: 'Simulation started' }));
      } catch (err) {
        simulationState.running = false;
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // --- API: Stop Simulation ---
  if (pathname === '/api/stop' && req.method === 'POST') {
    if (currentProcess && simulationState.running) {
      exec(`taskkill /pid ${currentProcess.pid} /t /f`, () => {});
      currentProcess = null;
      simulationState.running = false;
      simulationState.statusText = 'Simulation Aborted by User';
      addLog('[UI] Simulation stopped by user.');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'Simulation stopped' }));
    } else {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, message: 'No simulation running' }));
    }
    return;
  }

  // --- API: Make Video ---
  if (pathname === '/api/make-video' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const data = JSON.parse(body || '{}');
      const fps = parseInt(data.fps || 15);
      addLog(`[UI] Converting frames to MP4 (FPS: ${fps})...`);
      exec(`cmd.exe /c "D:\\MPM\\make_video.bat ${fps}"`, { cwd: WORKSPACE }, (error, stdout, stderr) => {
        addLog(stdout || stderr);
        if (error) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: error.message, output: stdout || stderr }));
        } else {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ success: true, message: 'Video rendered successfully', videoUrl: '/api/video' }));
        }
      });
    });
    return;
  }

  // --- Static Files Serving ---
  let filePath = path.join(UI_DIR, pathname === '/' ? 'index.html' : pathname);
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.json': 'application/json'
  };

  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('404 Not Found');
  }
});

server.listen(PORT, () => {
  console.log(`========================================================`);
  console.log(`CL-MPM Simulation Studio is running!`);
  console.log(`Open in Browser: http://localhost:${PORT}`);
  console.log(`========================================================`);
});
