/**
 * CL-MPM Studio - Frontend Controller
 * Full interactive workbench for Material Point Method simulations
 */

document.addEventListener('DOMContentLoaded', () => {
  // --- DOM Elements ---
  const presetSelect = document.getElementById('presetSelect');
  const statusBadge = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');
  const btnResetDefaults = document.getElementById('btnResetDefaults');
  const configForm = document.getElementById('configForm');
  const btnRun = document.getElementById('btnRun');
  const btnRunText = document.getElementById('btnRunText');
  const iconPlay = btnRun.querySelector('.icon-play');
  const iconSpinner = btnRun.querySelector('.icon-spinner');
  const btnStop = document.getElementById('btnStop');
  const btnHeaderVideo = document.getElementById('btnHeaderVideo');

  // Sliders & inputs
  const shelfHeightRange = document.getElementById('shelfHeightRange');
  const shelfHeight = document.getElementById('shelfHeight');
  const shelfAspectRange = document.getElementById('shelfAspectRange');
  const shelfAspect = document.getElementById('shelfAspect');
  const cliffSlopeRange = document.getElementById('cliffSlopeRange');
  const cliffSlope = document.getElementById('cliffSlope');
  const notchHeightRange = document.getElementById('notchHeightRange');
  const notchHeight = document.getElementById('notchHeight');
  const notchDepthRange = document.getElementById('notchDepthRange');
  const notchDepth = document.getElementById('notchDepth');
  const notchShape = document.getElementById('notchShape');
  const notchTipFraction = document.getElementById('notchTipFraction');
  const geometryPreview = document.getElementById('geometryPreview');
  const undercutRange = document.getElementById('undercutRange');
  const undercut = document.getElementById('undercut');
  const soilBoundary = document.getElementById('soilBoundary');
  const meshSize = document.getElementById('meshSize');
  const mpsPerCell = document.getElementById('mpsPerCell');
  const modulusERange = document.getElementById('modulusERange');
  const modulusE = document.getElementById('modulusE');
  const nu = document.getElementById('nu');
  const frictionAngle = document.getElementById('frictionAngle');
  const cohesion = document.getElementById('cohesion');
  const dilatancyAngle = document.getElementById('dilatancyAngle');
  const nonlocalLength = document.getElementById('nonlocalLength');
  const enablePlasticity = document.getElementById('enablePlasticity');
  const initStress = document.getElementById('initStress');
  const ductility = document.getElementById('ductility');
  const delayTime = document.getElementById('delayTime');
  const density = document.getElementById('density');
  const enableDamage = document.getElementById('enableDamage');
  const constitutiveModel = document.getElementById('constitutiveModel');
  const customModelTemplate = document.getElementById('customModelTemplate');
  const customModelSource = document.getElementById('customModelSource');
  const customModelFile = document.getElementById('customModelFile');
  const customModelNotice = document.getElementById('customModelNotice');
  const btnLoadModelTemplate = document.getElementById('btnLoadModelTemplate');
  const btnValidateModel = document.getElementById('btnValidateModel');
  const btnDownloadModel = document.getElementById('btnDownloadModel');
  const btnExportSimulation = document.getElementById('btnExportSimulation');
  const modelWorkspace = window.StudioModelWorkspace;
  const maxStepsRange = document.getElementById('maxStepsRange');
  const maxSteps = document.getElementById('maxSteps');
  const substeps = document.getElementById('substeps');
  const plotMode = document.getElementById('plotMode');
  const workers = document.getElementById('workers');

  // Progress
  const progressBarFill = document.getElementById('progressBarFill');
  const progressText = document.getElementById('progressText');
  const etaText = document.getElementById('etaText');

  // Frames & Viewport
  const frameCanvas = document.getElementById('frameCanvas');
  const currentFrameImg = document.getElementById('currentFrameImg');
  const emptyFramesState = document.getElementById('emptyFramesState');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const iconPlayState = btnPlayPause.querySelector('.icon-play');
  const iconPauseState = btnPlayPause.querySelector('.icon-pause');
  const currentFrameNum = document.getElementById('currentFrameNum');
  const totalFramesNum = document.getElementById('totalFramesNum');
  const frameScrubber = document.getElementById('frameScrubber');
  const playbackFps = document.getElementById('playbackFps');
  const btnRefreshFrames = document.getElementById('btnRefreshFrames');

  // Video & VTK
  const videoPlayer = document.getElementById('videoPlayer');
  const btnGenerateVideo = document.getElementById('btnGenerateVideo');
  const btnRefreshVtk = document.getElementById('btnRefreshVtk');
  const vtkFileList = document.getElementById('vtkFileList');

  // Terminal
  const logOutput = document.getElementById('logOutput');
  const autoScrollCheck = document.getElementById('autoScrollCheck');
  const btnClearLog = document.getElementById('btnClearLog');

  // --- State Variables ---
  let isRunning = false;
  let pollTimer = null;
  let isPlayingFrames = false;
  let playInterval = null;
  let frameList = [];
  let currentFrameIndex = -1;
  let lastLogSeq = 0;

  // --- Presets Definition ---
  const PRESETS = {
    default: {
      shelfHeight: 100,
      shelfAspect: 2.0,
      cliffSlope: 90,
      notchHeight: 0,
      notchDepth: 0,
      notchShape: 'rectangle',
      notchTipFraction: 0.5,
      undercut: 0,
      soilBoundary: 20,
      meshSize: "5.0",
      mpsPerCell: "2",
      modulusE: 1.0,
      nu: 0.35,
      frictionAngle: 40,
      initStress: 200,
      ductility: 10,
      cohesion: 1000,
      dilatancyAngle: 0,
      nonlocalLength: 3 * Math.sqrt(7),
      enablePlasticity: true,
      delayTime: 10,
      density: 1700,
      enableDamage: true,
      maxSteps: 50,
      substeps: 10,
      plotMode: 'stress',
      workers: 4
    },
    sloped: {
      shelfHeight: 100,
      shelfAspect: 2.0,
      cliffSlope: 75,
      notchHeight: 0,
      notchDepth: 0,
      notchShape: 'rectangle',
      notchTipFraction: 0.5,
      undercut: 0,
      soilBoundary: 20,
      meshSize: "5.0",
      mpsPerCell: "2",
      modulusE: 1.0,
      nu: 0.35,
      frictionAngle: 40,
      initStress: 200,
      ductility: 10,
      cohesion: 1000,
      dilatancyAngle: 0,
      nonlocalLength: 3 * Math.sqrt(7),
      enablePlasticity: true,
      delayTime: 10,
      density: 1700,
      enableDamage: true,
      maxSteps: 50,
      substeps: 10,
      plotMode: 'stress',
      workers: 4
    },
    undercut: {
      shelfHeight: 100,
      shelfAspect: 2.0,
      cliffSlope: 90,
      notchHeight: 10,
      notchDepth: 15,
      notchShape: 'rectangle',
      notchTipFraction: 0.5,
      undercut: 15,
      soilBoundary: 20,
      meshSize: "5.0",
      mpsPerCell: "2",
      modulusE: 1.0,
      nu: 0.35,
      frictionAngle: 40,
      initStress: 200,
      ductility: 10,
      cohesion: 1000,
      dilatancyAngle: 0,
      nonlocalLength: 3 * Math.sqrt(7),
      enablePlasticity: true,
      delayTime: 10,
      density: 1700,
      enableDamage: true,
      maxSteps: 50,
      substeps: 10,
      plotMode: 'stress',
      workers: 4
    },
    elastic: {
      shelfHeight: 80,
      shelfAspect: 2.0,
      cliffSlope: 85,
      notchHeight: 0,
      notchDepth: 0,
      notchShape: 'rectangle',
      notchTipFraction: 0.5,
      undercut: 0,
      soilBoundary: 20,
      meshSize: "5.0",
      mpsPerCell: "2",
      modulusE: 2.0,
      nu: 0.30,
      frictionAngle: 45,
      initStress: 1000,
      ductility: 20,
      cohesion: 1000,
      dilatancyAngle: 0,
      nonlocalLength: 3 * Math.sqrt(7),
      enablePlasticity: false,
      delayTime: 10,
      density: 1800,
      enableDamage: false,
      maxSteps: 30,
      substeps: 10,
      plotMode: 'stress',
      workers: 4
    },
    quick: {
      shelfHeight: 60,
      shelfAspect: 1.5,
      cliffSlope: 80,
      notchHeight: 5,
      notchDepth: 8,
      notchShape: 'rectangle',
      notchTipFraction: 0.5,
      undercut: 0,
      soilBoundary: 15,
      meshSize: "10.0",
      mpsPerCell: "1",
      modulusE: 1.0,
      nu: 0.35,
      frictionAngle: 40,
      initStress: 200,
      ductility: 10,
      cohesion: 1000,
      dilatancyAngle: 0,
      nonlocalLength: 3 * Math.sqrt(7),
      enablePlasticity: true,
      delayTime: 10,
      density: 1700,
      enableDamage: true,
      maxSteps: 10,
      substeps: 5,
      plotMode: 'stress',
      workers: 4
    }
  };

  // --- Two-way Slider Syncing ---
  function syncInputs(slider, numberInput) {
    slider.addEventListener('input', () => {
      numberInput.value = slider.value;
    });
    numberInput.addEventListener('input', () => {
      if (numberInput.value !== '') {
        slider.value = numberInput.value;
      }
    });
  }

  syncInputs(shelfHeightRange, shelfHeight);
  syncInputs(shelfAspectRange, shelfAspect);
  syncInputs(cliffSlopeRange, cliffSlope);
  syncInputs(notchHeightRange, notchHeight);
  syncInputs(notchDepthRange, notchDepth);
  syncInputs(undercutRange, undercut);
  syncInputs(modulusERange, modulusE);
  syncInputs(maxStepsRange, maxSteps);

  // Live geometry previews Lisp's clipping predicates; it is not an MPM result.
  function updateGeometryPreview() {
    const raw = {
      shelfHeight: Number(shelfHeight.value),
      shelfAspect: Number(shelfAspect.value),
      cliffSlope: Number(cliffSlope.value),
      undercut: Number(undercut.value),
      soilBoundary: Number(soilBoundary.value),
      notchHeight: Number(notchHeight.value),
      notchDepth: Number(notchDepth.value),
      notchShape: notchShape.value,
      notchTipFraction: Number(notchTipFraction.value)
    };
    notchTipFraction.disabled = notchShape.value !== 'triangle';
    geometryPreview.innerHTML = window.CliffGeometry.previewMarkup(raw);
  }

  [shelfHeight, shelfHeightRange, shelfAspect, shelfAspectRange,
   cliffSlope, cliffSlopeRange, undercut, undercutRange,
   soilBoundary, notchHeight, notchHeightRange, notchDepth,
   notchDepthRange, notchShape, notchTipFraction].forEach(control => {
    control.addEventListener('input', updateGeometryPreview);
    control.addEventListener('change', updateGeometryPreview);
  });
  updateGeometryPreview();

  // --- Tab Switching: Parameter Panel ---
  const paramTabs = document.querySelectorAll('.param-tab');
  paramTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      paramTabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(`tab-${tab.dataset.tab}`);
      if (target) target.classList.add('active');
    });
  });

  // --- Tab Switching: Viewport ---
  const vtabs = document.querySelectorAll('.vtab');
  vtabs.forEach(tab => {
    tab.addEventListener('click', () => {
      vtabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.vtab-pane').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const pane = document.getElementById(`pane-${tab.dataset.vtab}`);
      if (pane) pane.classList.add('active');

      if (tab.dataset.vtab === 'vtk') {
        loadVtkFiles();
      }
    });
  });

  // --- Presets Application ---
  function applyPreset(name) {
    const p = PRESETS[name];
    if (!p) return;

    shelfHeight.value = p.shelfHeight; shelfHeightRange.value = p.shelfHeight;
    shelfAspect.value = p.shelfAspect; shelfAspectRange.value = p.shelfAspect;
    cliffSlope.value = p.cliffSlope; cliffSlopeRange.value = p.cliffSlope;
    notchHeight.value = p.notchHeight; notchHeightRange.value = p.notchHeight;
    notchDepth.value = p.notchDepth; notchDepthRange.value = p.notchDepth;
    notchShape.value = p.notchShape;
    notchTipFraction.value = p.notchTipFraction;
    undercut.value = p.undercut; undercutRange.value = p.undercut;
    soilBoundary.value = p.soilBoundary;
    meshSize.value = p.meshSize;
    mpsPerCell.value = p.mpsPerCell;
    modulusE.value = p.modulusE; modulusERange.value = p.modulusE;
    nu.value = p.nu;
    frictionAngle.value = p.frictionAngle;
    initStress.value = p.initStress;
    ductility.value = p.ductility;
    cohesion.value = p.cohesion;
    dilatancyAngle.value = p.dilatancyAngle;
    nonlocalLength.value = p.nonlocalLength;
    enablePlasticity.checked = p.enablePlasticity;
    delayTime.value = p.delayTime;
    density.value = p.density;
    enableDamage.checked = p.enableDamage;
    constitutiveModel.value = 'chalk';
    maxSteps.value = p.maxSteps; maxStepsRange.value = p.maxSteps;
    substeps.value = p.substeps;
    plotMode.value = p.plotMode;
    workers.value = p.workers;
    updateGeometryPreview();

    appendLog(`[Preset] Loaded configuration preset: "${name.toUpperCase()}"`);
  }

  presetSelect.addEventListener('change', (e) => applyPreset(e.target.value));
  btnResetDefaults.addEventListener('click', () => {
    presetSelect.value = 'default';
    applyPreset('default');
  });

  // --- Logging Functions ---
  function appendLog(text) {
    logOutput.textContent += `\n${text}`;
    if (autoScrollCheck.checked) {
      const tb = document.getElementById('terminalBody');
      tb.scrollTop = tb.scrollHeight;
    }
  }

  btnClearLog.addEventListener('click', () => {
    logOutput.textContent = '// Terminal cleared.';
  });

  // --- Fetch API: Status & Polling ---
  async function pollStatus() {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) return;
      const data = await res.json();

      updateEngineState(data);

      // Fetch new log lines (cursor based: server returns {lines, next})
      const logRes = await fetch(`/api/logs?since=${lastLogSeq}`);
      if (logRes.ok) {
        const logData = await logRes.json();
        if (Array.isArray(logData.lines)) {
          logData.lines.forEach(line => appendLog(String(line).trim()));
        }
        if (Number.isFinite(logData.next)) lastLogSeq = logData.next;
      }

      // If frames are being produced, refresh frames list
      if (data.running) {
        await loadFrames(true);
      } else if (isRunning && !data.running) {
        // Stopped or completed
        isRunning = false;
        setRunningUI(false);
        await loadFrames(false);
        loadVtkFiles();
      }
    } catch (e) {
      console.warn('Status poll warning:', e);
    }
  }

  function updateEngineState(state) {
    if (state.running) {
      statusBadge.className = 'status-indicator running';
      statusText.textContent = state.statusText || 'Simulating...';
      progressBarFill.style.width = `${state.percent || 0}%`;
      progressText.textContent = `${state.percent || 0}% (${state.step || 0} / ${state.totalSteps || 0} steps)`;
      
      if (state.startTime && state.step > 0) {
        const elapsedSec = (Date.now() - state.startTime) / 1000;
        const secPerStep = elapsedSec / state.step;
        const remSec = Math.round((state.totalSteps - state.step) * secPerStep);
        etaText.textContent = `ETA: ~${remSec}s`;
      } else {
        etaText.textContent = 'Calculating...';
      }
    } else {
      if (state.percent === 100) {
        statusBadge.className = 'status-indicator success';
        statusText.textContent = 'Done (100%)';
        progressBarFill.style.width = '100%';
        progressText.textContent = `100% (${state.totalSteps} steps completed)`;
        etaText.textContent = 'Finished';
      } else {
        statusBadge.className = 'status-indicator';
        statusText.textContent = state.statusText || 'Engine Ready';
        etaText.textContent = 'Idle';
      }
    }
  }

  function setRunningUI(running) {
    isRunning = running;
    if (running) {
      btnRun.disabled = true;
      iconPlay.classList.add('hide');
      iconSpinner.classList.remove('hide');
      btnRunText.textContent = 'Menghitung Fisika MPM...';
      btnStop.classList.remove('hide');
      statusBadge.className = 'status-indicator running';
      statusText.textContent = 'Running...';
    } else {
      btnRun.disabled = false;
      iconPlay.classList.remove('hide');
      iconSpinner.classList.add('hide');
      btnRunText.textContent = 'Jalankan Simulasi';
      btnStop.classList.add('hide');
    }
  }

  // --- Local Lisp workspace: editing and export never execute model code.
  function setModelNotice(message) {
    customModelNotice.textContent = message;
  }
  function downloadText(filename, content) {
    const url = URL.createObjectURL(new Blob([content], { type: 'text/plain;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  btnLoadModelTemplate.addEventListener('click', () => {
    if (customModelSource.value.trim() &&
        !confirm('Ganti kode editor dengan template? Kode lama di editor akan tertimpa.')) return;
    customModelSource.value = modelWorkspace.TEMPLATES[customModelTemplate.value];
    setModelNotice('Template berhasil dimuat. Ini belum divalidasi oleh compiler SBCL.');
  });
  customModelFile.addEventListener('change', async () => {
    const file = customModelFile.files && customModelFile.files[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.lisp') ||
        file.size > modelWorkspace.MAX_SOURCE_BYTES) {
      return setModelNotice('Hanya file .lisp berukuran maksimal 32 KiB yang diterima.');
    }
    if (customModelSource.value.trim() &&
        !confirm('Import akan menimpa kode editor. Lanjutkan?')) return;
    customModelSource.value = await file.text();
    constitutiveModel.value = 'custom';
    setModelNotice('File dimuat ke editor lokal; belum dieksekusi atau diunggah.');
  });
  btnValidateModel.addEventListener('click', () => {
    const result = modelWorkspace.validateSource(customModelSource.value);
    setModelNotice(result.message);
  });
  btnDownloadModel.addEventListener('click', () => {
    if (!customModelSource.value.trim()) return setModelNotice('Kode .lisp masih kosong.');
    downloadText('custom-model.lisp', customModelSource.value);
    setModelNotice('custom-model.lisp berhasil disiapkan untuk download.');
  });
  btnExportSimulation.addEventListener('click', () => {
    try {
      downloadText('simulation.lisp', modelWorkspace.exportRunScript(collectSimulationParams()));
      setModelNotice('simulation.lisp diekspor. Jika memilih custom, ekspor custom-model.lisp juga.');
    } catch (err) {
      setModelNotice('Gagal export: ' + err.message);
    }
  });
  fetch('/api/custom-model-capabilities').then(r => r.json()).then(data => {
    if (!data.enabled) {
      setModelNotice('Editor dan export aktif; eksekusi custom dinonaktifkan (STUDIO_ALLOW_CUSTOM_LISP=1 untuk localhost).');
    }
  }).catch(() => {});

  // --- Run Simulation Trigger ---
  function collectSimulationParams() {
    return {
      shelfHeight: parseFloat(shelfHeight.value) || 100,
      shelfAspect: parseFloat(shelfAspect.value) || 2.0,
      cliffSlope: parseFloat(cliffSlope.value) || 90,
      notchHeight: parseFloat(notchHeight.value) || 0,
      notchDepth: parseFloat(notchDepth.value) || 0,
      notchShape: notchShape.value,
      notchTipFraction: Number(notchTipFraction.value),
      soilBoundary: Number(soilBoundary.value),
      meshSize: parseFloat(meshSize.value) || 5.0,
      mpsPerCell: parseInt(mpsPerCell.value) || 2,
      undercut: parseFloat(undercut.value) || 0,
      E: (parseFloat(modulusE.value) || 1.0) * 1e9,
      nu: parseFloat(nu.value) || 0.35,
      frictionAngle: parseFloat(frictionAngle.value) || 40,
      cohesion: Number(cohesion.value) * 1e3,
      dilatancyAngle: Number(dilatancyAngle.value),
      nonlocalLength: Number(nonlocalLength.value),
      enablePlasticity: enablePlasticity.checked,
      initiationStress: (parseFloat(initStress.value) || 200) * 1e3,
      ductility: parseFloat(ductility.value) || 10,
      density: parseFloat(density.value) || 1700,
      enableDamage: enableDamage.checked,
      maxSteps: parseInt(maxSteps.value) || 10,
      substeps: parseInt(substeps.value) || 10,
      plotMode: plotMode.value || 'stress',
      workers: parseInt(workers.value) || 4,
      delayTime: Number(delayTime.value),
      constitutiveModel: constitutiveModel.value
    };
  }

  async function handleRunSimulation() {
    console.log('[CL-MPM] handleRunSimulation triggered');
    if (isRunning) return;
    const payload = collectSimulationParams();
    if (payload.constitutiveModel === 'custom') {
      const check = modelWorkspace.validateSource(customModelSource.value);
      if (!check.ok) return setModelNotice(check.message);
      if (!confirm('Custom Lisp akan dieksekusi dengan hak akses OS user lokal, TANPA sandbox. Jalankan kode ini?')) return;
      payload.customModelSource = customModelSource.value;
      payload.confirmCustomExecution = true;
    }

    setRunningUI(true);
    lastLogSeq = 0;
    progressBarFill.style.width = '0%';
    progressText.textContent = `0% (0 / ${payload.maxSteps} steps)`;
    etaText.textContent = 'Memulai proses...';

    // Switch to Live Frames tab
    const framesTab = document.querySelector('.vtab[data-vtab="frames"]');
    if (framesTab) framesTab.click();

    try {
      appendLog(`[Client] Mengirim parameter simulasi ke server...`);
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Gagal memulai simulasi di server');
      }
      appendLog(`[Client] Simulasi berhasil dimulai pada engine SBCL.`);
      
      // Start polling
      if (pollTimer) clearInterval(pollTimer);
      pollTimer = setInterval(pollStatus, 800);
    } catch (err) {
      alert(`Error saat menjalankan simulasi: ${err.message}`);
      setRunningUI(false);
      appendLog(`[Client Error] ${err.message}`);
    }
  }

  btnRun.addEventListener('click', handleRunSimulation);
  configForm.addEventListener('submit', (e) => {
    e.preventDefault();
    handleRunSimulation();
  });

  // --- Stop Simulation ---
  btnStop.addEventListener('click', async () => {
    if (!confirm('Hentikan proses simulasi yang sedang berjalan?')) return;
    try {
      appendLog(`[Client] Requesting simulation termination...`);
      const res = await fetch('/api/stop', { method: 'POST' });
      const data = await res.json();
      appendLog(`[Client] ${data.message}`);
    } catch (err) {
      appendLog(`[Client Error] Failed to stop simulation: ${err.message}`);
    }
  });

  // --- Frames Management & Playback ---
  async function loadFrames(autoAdvance = false) {
    try {
      const res = await fetch('/api/frames');
      if (!res.ok) return;
      const data = await res.json();
      const oldLength = frameList.length;
      frameList = data.frames || [];

      if (frameList.length === 0) {
        currentFrameImg.classList.add('hide');
        emptyFramesState.classList.remove('hide');
        frameScrubber.max = 0;
        frameScrubber.value = 0;
        currentFrameNum.textContent = 0;
        totalFramesNum.textContent = 0;
        currentFrameIndex = -1;
        return;
      }

      emptyFramesState.classList.add('hide');
      currentFrameImg.classList.remove('hide');

      frameScrubber.min = 1;
      frameScrubber.max = frameList.length;
      totalFramesNum.textContent = frameList.length;

      // If new frames came in or first load
      if (currentFrameIndex === -1 || (autoAdvance && frameList.length > oldLength)) {
        showFrame(frameList.length - 1);
      }
    } catch (err) {
      console.error('Error loading frames:', err);
    }
  }

  function showFrame(index) {
    if (index < 0 || index >= frameList.length) return;
    currentFrameIndex = index;
    const frameName = frameList[index];
    currentFrameImg.src = `/api/frame/${frameName}?t=${Date.now()}`;
    frameScrubber.value = index + 1;
    currentFrameNum.textContent = index + 1;
  }

  // Scrubber user interaction
  frameScrubber.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    if (val >= 1 && val <= frameList.length) {
      showFrame(val - 1);
    }
  });

  // Play / Pause animation
  function togglePlayPause() {
    if (isPlayingFrames) {
      stopPlayback();
    } else {
      startPlayback();
    }
  }

  function startPlayback() {
    if (frameList.length <= 1) return;
    isPlayingFrames = true;
    iconPlayState.classList.add('hide');
    iconPauseState.classList.remove('hide');

    const fps = parseInt(playbackFps.value || 10);
    const intervalMs = Math.max(20, Math.round(1000 / fps));

    if (playInterval) clearInterval(playInterval);
    playInterval = setInterval(() => {
      let nextIndex = currentFrameIndex + 1;
      if (nextIndex >= frameList.length) {
        nextIndex = 0; // loop
      }
      showFrame(nextIndex);
    }, intervalMs);
  }

  function stopPlayback() {
    isPlayingFrames = false;
    iconPlayState.classList.remove('hide');
    iconPauseState.classList.add('hide');
    if (playInterval) {
      clearInterval(playInterval);
      playInterval = null;
    }
  }

  btnPlayPause.addEventListener('click', togglePlayPause);
  playbackFps.addEventListener('change', () => {
    if (isPlayingFrames) {
      stopPlayback();
      startPlayback();
    }
  });

  btnRefreshFrames.addEventListener('click', () => loadFrames(false));

  // Keyboard navigation for scrubber (Arrow Left / Right, Space for Play/Pause)
  window.addEventListener('keydown', (e) => {
    // Only if not focused on input or textarea
    if (['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;

    if (e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.code === 'ArrowLeft') {
      e.preventDefault();
      stopPlayback();
      if (currentFrameIndex > 0) showFrame(currentFrameIndex - 1);
    } else if (e.code === 'ArrowRight') {
      e.preventDefault();
      stopPlayback();
      if (currentFrameIndex < frameList.length - 1) showFrame(currentFrameIndex + 1);
    }
  });

  // --- Video Conversion & Player ---
  async function renderVideo() {
    const fps = parseInt(playbackFps.value || 15);
    appendLog(`[Video] Starting FFmpeg video rendering at ${fps} FPS...`);
    btnGenerateVideo.disabled = true;
    btnHeaderVideo.disabled = true;

    try {
      const res = await fetch('/api/make-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fps })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Video creation failed');

      appendLog(`[Video] Success! Video created (${data.videoUrl || '/api/video'})`);
      
      // Switch to video pane
      document.querySelector('.vtab[data-vtab="video"]').click();
      
      // Reload video player
      videoPlayer.src = `/api/video?t=${Date.now()}`;
      videoPlayer.load();
      videoPlayer.play().catch(() => {});
    } catch (err) {
      alert(`Error rendering video: ${err.message}`);
      appendLog(`[Video Error] ${err.message}`);
    } finally {
      btnGenerateVideo.disabled = false;
      btnHeaderVideo.disabled = false;
    }
  }

  btnGenerateVideo.addEventListener('click', renderVideo);
  btnHeaderVideo.addEventListener('click', renderVideo);

  // --- VTK Files Explorer ---
  async function loadVtkFiles() {
    try {
      vtkFileList.innerHTML = '<div class="empty-hint">Memuat file VTK...</div>';
      const res = await fetch('/api/output-files');
      if (!res.ok) return;
      const data = await res.json();
      const files = data.files || [];

      if (files.length === 0) {
        vtkFileList.innerHTML = `<div class="empty-hint">Belum ada file .vtk di folder ${data.directory || 'output/studio/vtk'}</div>`;
        return;
      }

      vtkFileList.innerHTML = files
        .filter(f => f.name.endsWith('.vtk'))
        .sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }))
        .map(f => {
          const kb = Math.round(f.sizeBytes / 1024);
          const dateStr = new Date(f.modified).toLocaleTimeString();
          return `
            <div class="vtk-file-card">
              <div class="vtk-file-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
              </div>
              <div class="vtk-file-details">
                <span class="vtk-file-name">${f.name}</span>
                <span class="vtk-file-meta">${kb} KB • ${dateStr}</span>
              </div>
            </div>
          `;
        }).join('');
    } catch (err) {
      console.error('Error fetching VTK files:', err);
      vtkFileList.innerHTML = `<div class="empty-hint text-danger">Gagal memuat: ${err.message}</div>`;
    }
  }

  btnRefreshVtk.addEventListener('click', loadVtkFiles);

  // --- Initial Startup ---
  loadFrames();
  pollStatus();
  pollTimer = setInterval(pollStatus, 1500);
});
