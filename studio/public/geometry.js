/**
 * Lightweight, deterministic 2D geometry preview for CL-MPM Studio.
 * This approximates scenario.lisp particle-removal predicates at a finite
 * visual sampling resolution; it does not run the MPM solver.
 *
 * The face is anchored at (shelfLength, soilBoundary). The face formula
 * matches the plane-point-sdf normal in studio/lisp/scenario.lisp.
 * Notches are centred on that anchor, as in the Lisp scenario.
 */
'use strict';

(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.CliffGeometry = api;
}(typeof window !== 'undefined' ? window : null, function () {
  function config(raw) {
    const defaults = {
      shelfHeight: 100, shelfAspect: 2, soilBoundary: 20,
      cliffSlope: 90, undercut: 0, notchHeight: 0, notchDepth: 0,
      notchShape: 'rectangle', notchTipFraction: 0.5,
    };
    const result = {};
    for (const [key, fallback] of Object.entries(defaults)) {
      if (key === 'notchShape') {
        result[key] = ['rectangle', 'ellipse', 'triangle'].includes(raw[key]) ? raw[key] : fallback;
      } else {
        const n = Number(raw[key]);
        result[key] = raw[key] === '' || raw[key] == null || !Number.isFinite(n) ? fallback : n;
      }
    }
    return result;
  }

  function dimensions(raw) {
    const p = config(raw);
    const height = Math.max(0.001, p.shelfHeight);
    const soil = Math.max(0, p.soilBoundary);
    const shelf = height * Math.max(0.001, p.shelfAspect);
    return { ...p, height, soil, shelf, width: shelf + 2 * height, top: soil + height };
  }

  function faceX(g, y) {
    return g.shelf - (y - g.soil) * Math.tan((90 - g.cliffSlope - g.undercut) * Math.PI / 180);
  }

  function notchContains(g, x, y) {
    const h = g.notchHeight;
    if (!(h > 0.01) || y <= g.soil || y >= g.soil + h) return false;
    const d = g.notchDepth > 0.01 ? g.notchDepth : 1.5 * h;
    const dy = y - (g.soil + h / 2);
    const dx = x - g.shelf;
    switch (g.notchShape) {
      case 'rectangle':
        return Math.abs(dx) < d;
      case 'ellipse':
        return (dx / d) ** 2 + (dy / (h / 2)) ** 2 < 1;
      case 'triangle': {
        const tipY = g.soil + h * g.notchTipFraction;
        const fraction = y < tipY
          ? (y - g.soil) / (tipY - g.soil)
          : (g.soil + h - y) / (g.soil + h - tipY);
        return x > g.shelf - d * fraction && x < g.shelf;
      }
      default: return false;
    }
  }

  function materialContains(g, x, y) {
    if (x < 0 || x > g.width || y < 0 || y > g.top) return false;
    if (y <= g.soil) return true;
    return x < faceX(g, y) && !notchContains(g, x, y);
  }

  function previewMarkup(raw, opts = {}) {
    const g = dimensions(raw);
    const cols = opts.cols || 180;
    const rows = opts.rows || 90;
    const w = 900;
    const h = 360;
    const cellW = w / cols;
    const cellH = h / rows;
    const segments = [];
    for (let row = 0; row < rows; row++) {
      const y = g.top * (1 - (row + 0.5) / rows);
      let begin = -1;
      for (let col = 0; col <= cols; col++) {
        const solid = col < cols && materialContains(g, (col + 0.5) * g.width / cols, y);
        if (solid && begin < 0) begin = col;
        if (!solid && begin >= 0) {
          const left = begin * cellW;
          const top = row * cellH;
          segments.push('M' + left.toFixed(2) + ',' + top.toFixed(2) +
            'h' + ((col - begin) * cellW).toFixed(2) +
            'v' + cellH.toFixed(2) +
            'h-' + ((col - begin) * cellW).toFixed(2) + 'z');
          begin = -1;
        }
      }
    }
    const soilLine = h * (1 - g.soil / g.top);
    const face = (g.shelf / g.width) * w;
    return `<rect width="${w}" height="${h}" rx="6" fill="#0d1d35"/>
      <path d="${segments.join(' ')}" fill="#8cb7ca"/>
      <line x1="0" y1="${soilLine.toFixed(2)}" x2="${w}"
            y2="${soilLine.toFixed(2)}" stroke="#ecae61" stroke-width="1.5"
            stroke-dasharray="7 5"/>
      <line x1="${face.toFixed(2)}" y1="${soilLine.toFixed(2)}"
            x2="${face.toFixed(2)}" y2="${Math.max(0,soilLine-20).toFixed(2)}"
            stroke="#e7f4ff" stroke-width="1.5" stroke-dasharray="4 4"/>
      <text x="14" y="24" fill="#eef6ff" font-size="15">GEOMETRY PREVIEW · NOT A SOLVER RESULT</text>
      <text x="14" y="${Math.max(16,soilLine-7).toFixed(2)}" fill="#ecae61" font-size="13">Base layer</text>
      <text x="${w-12}" y="${h-12}" text-anchor="end" fill="#dbeafe" font-size="13">${g.height.toFixed(1)} m cliff · ${g.notchShape} notch</text>`;
  }

  return { config, dimensions, faceX, notchContains, materialContains, previewMarkup };
}));
