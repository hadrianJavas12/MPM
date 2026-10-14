'use strict';
/**
 * Standalone Studio custom-material authoring helpers.
 * Browser: window.StudioModelWorkspace; Node tests: require('./model-workspace.js').
 * Validation here is LEXICAL only and MUST NOT be treated as a Lisp sandbox.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.StudioModelWorkspace = api;
}(typeof window !== 'undefined' ? window : null, function () {
  const MAX_SOURCE_BYTES = 32 * 1024;

  const TEMPLATES = Object.freeze({
    delegate: `;;;; Studio custom chalk model — starting point.
;;;; This method is invoked for each particle update. The superclass
;;;; implements the existing chalk plastic-damage constitutive response.
;;;; Modify it carefully; validate against analytical and reference cases.
(in-package :cl-mpm-studio)
(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  (call-next-method))
`,
    elastic: `;;;; Experimental elastic constitutive update for Studio chalk particles.
;;;; CAUTION: replaces the standard chalk plastic stress update.
;;;; Damage evolution elsewhere may still be active unless disabled in Studio.
(in-package :cl-mpm-studio)
(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  (let ((stress (cl-mpm/particle::mp-stress mp))
        (elastic (cl-mpm/particle::mp-elastic-matrix mp)))
    ;; STRESS and STRAIN are Voigt matrices supplied by CL-MPM.
    (cl-mpm/utils:voigt-copy-into
     (cl-mpm/constitutive::linear-elastic-mat strain elastic)
     stress)
    stress))
`
  });

  function validateSource(source) {
    if (typeof source !== 'string' || !source.trim()) return { ok: false, message: 'Source .lisp belum diisi.' };
    if (new TextEncoder().encode(source).byteLength > MAX_SOURCE_BYTES)
      return { ok: false, message: 'Source melewati batas 32 KiB.' };
    if (source.includes('\0')) return { ok: false, message: 'NUL byte tidak diizinkan.' };
    // Check balanced delimiters outside strings, line comments and #|...|# comments.
    let depth = 0, inString = false, escaped = false, inLineComment = false, blockDepth = 0;
    for (let i = 0; i < source.length; i++) {
      const c = source[i], next = source[i + 1];
      if (inLineComment) { if (c === '\n') inLineComment = false; continue; }
      if (blockDepth) {
        if (c === '#' && next === '|') { blockDepth++; i++; }
        else if (c === '|' && next === '#') { blockDepth--; i++; }
        continue;
      }
      if (inString) {
        if (escaped) escaped = false;
        else if (c === '\\') escaped = true;
        else if (c === '"') inString = false;
        continue;
      }
      if (c === ';') { inLineComment = true; continue; }
      if (c === '#' && next === '|') { blockDepth++; i++; continue; }
      if (c === '"') { inString = true; continue; }
      if (c === '(') depth++;
      if (c === ')') { depth--; if (depth < 0) return { ok: false, message: 'Terdapat kurung tutup berlebih.' }; }
    }
    if (inString || blockDepth || depth)
      return { ok: false, message: 'String, komentar blok, atau tanda kurung belum tertutup.' };
    return { ok: true, message: 'Pemeriksaan leksikal lolos; kompilasi Lisp belum diuji.' };
  }

  function lispValue(value, key) {
    if (typeof value === 'boolean') return value ? 't' : 'nil';
    if (typeof value === 'number' && Number.isFinite(value)) {
      if (['maxSteps', 'substeps', 'workers', 'mpsPerCell'].includes(key)) {
        return String(Math.round(value));
      }
      const decimal = String(value);
      return (decimal.includes('e') ? decimal.replace(/e/i, 'd') : decimal + 'd0');
    }
    if (key === 'constitutiveModel' && ['chalk', 'custom'].includes(value)) return ':' + value;
    if (key === 'notchShape' && ['rectangle', 'ellipse', 'triangle'].includes(value)) return ':' + value;
    if (key === 'plotMode' && ['stress', 'damage', 'velocity'].includes(value)) return ':' + value;
    throw new Error('Parameter tidak dapat diekspor: ' + key);
  }

  const ALLOWED_KEYS = new Set([
    'shelfHeight', 'shelfAspect', 'cliffSlope', 'undercut', 'notchHeight',
    'notchDepth', 'notchShape', 'notchTipFraction', 'soilBoundary', 'meshSize',
    'mpsPerCell', 'density', 'E', 'nu', 'frictionAngle', 'ductility',
    'initiationStress', 'delayTime', 'enableDamage', 'maxSteps',
    'substeps', 'plotMode', 'workers', 'enablePlasticity', 'cohesion',
    'dilatancyAngle', 'nonlocalLength', 'constitutiveModel'
  ]);

  function exportRunScript(params) {
    const lines = [];
    for (const [key, value] of Object.entries(params || {})) {
      if (!ALLOWED_KEYS.has(key)) continue;
      lines.push('  (setf (gethash "' + key + '" config) ' + lispValue(value, key) + ')');
    }
    return `;;;; Exported from CL-MPM Studio. Requires the CL-MPM / Quicklisp environment.
;;;; Run from repository root; keep custom-model.lisp beside this script
;;;; when constitutiveModel = custom. No arbitrary source is loaded otherwise.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio)
(let ((config (cl-mpm-studio:load-config)))
${lines.join('\n')}
  (when (eq (gethash "constitutiveModel" config) :custom)
    (load (merge-pathnames "custom-model.lisp"
                           (uiop:pathname-directory-pathname *load-truename*))))
  (cl-mpm-studio:run config (uiop:ensure-directory-pathname #p"output/studio-export/")))
`;
  }

  return { MAX_SOURCE_BYTES, TEMPLATES, validateSource, exportRunScript };
}));
