'use strict';
/**
 * Standalone Studio custom-material authoring helpers.
 * Browser: window.StudioModelWorkspace; Node tests: require('./model-workspace.js').
 * Validation here is LEXICAL only and MUST NOT be treated as a Lisp sandbox.
 */
(function (root, factory) {
  const node = typeof module === 'object' && module.exports;
  const api = factory(node ? require('./config.js') : root.StudioConfig,
    node ? require('../schema.json').parameters : null);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.StudioModelWorkspace = api;
}(typeof window !== 'undefined' ? window : null, function (configApi, defaultSchema) {
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
;;;; Use only with plasticity and damage disabled and zero initial damage.
(in-package :cl-mpm-studio)
(defmethod cl-mpm/particle:constitutive-model
    ((mp studio-custom-chalk) strain dt)
  (declare (ignore dt))
  (when (or (cl-mpm/particle::mp-enable-plasticity mp)
            (cl-mpm/particle::mp-enable-damage mp)
            (plusp (cl-mpm/particle:mp-damage mp)))
    (error "Elastic template requires plasticity/damage off and zero damage."))
  (let ((stress (cl-mpm/particle::mp-stress-kirchoff mp))
        (undamaged (cl-mpm/particle::mp-undamaged-stress mp))
        (elastic (cl-mpm/particle::mp-elastic-matrix mp)))
    ;; STRAIN is elastic trial Hencky strain, not a strain increment.
    ;; Return Kirchhoff stress; the engine converts it to Cauchy stress.
    (cl-mpm/constitutive::linear-elastic-mat strain elastic undamaged)
    (cl-mpm/utils:voigt-copy-into
     undamaged stress)
    stress))
`
  });

  function validateSource(source) {
    if (typeof source !== 'string' || !source.trim()) return { ok: false, message: 'Source .lisp belum diisi.' };
    if (new TextEncoder().encode(source).byteLength > MAX_SOURCE_BYTES)
      return { ok: false, message: 'Source melewati batas 32 KiB.' };
    if (source.includes('\0')) return { ok: false, message: 'NUL byte tidak diizinkan.' };
    // Check balanced delimiters outside strings, line comments and #|...|# comments.
    let depth = 0, inString = false, inSymbol = false, escaped = false, inLineComment = false, blockDepth = 0;
    for (let i = 0; i < source.length; i++) {
      const c = source[i], next = source[i + 1];
      if (inLineComment) { if (c === '\n' || c === '\r') inLineComment = false; continue; }
      if (blockDepth) {
        if (c === '#' && next === '|') { blockDepth++; i++; }
        else if (c === '|' && next === '#') { blockDepth--; i++; }
        continue;
      }
      if (inString || inSymbol) {
        if (escaped) escaped = false;
        else if (c === '\\') escaped = true;
        else if (inString && c === '"') inString = false;
        else if (inSymbol && c === '|') inSymbol = false;
        continue;
      }
      if (c === ';') { inLineComment = true; continue; }
      if (c === '#' && next === '|') { blockDepth++; i++; continue; }
      // #\ followed by a delimiter is a character, not a string/comment/paren.
      if (c === '#' && next === '\\') {
        i += 2;
        if (i >= source.length) return { ok: false, message: 'Literal karakter #\\ belum lengkap.' };
        while (i + 1 < source.length && !/[\s()";|]/.test(source[i + 1])) i++;
        continue;
      }
      if (c === '\\') {
        if (++i >= source.length) return { ok: false, message: 'Escape simbol belum lengkap.' };
        continue;
      }
      if (c === '|') { inSymbol = true; continue; }
      if (c === '"') { inString = true; continue; }
      if (c === '(') depth++;
      if (c === ')') { depth--; if (depth < 0) return { ok: false, message: 'Terdapat kurung tutup berlebih.' }; }
    }
    if (inString || inSymbol || blockDepth || depth)
      return { ok: false, message: 'String, komentar blok, atau tanda kurung belum tertutup.' };
    return { ok: true, message: 'Pemeriksaan leksikal lolos; kompilasi Lisp belum diuji.' };
  }

  function lispValue(value, spec, key) {
    if (typeof value === 'boolean') return value ? 't' : 'nil';
    if (typeof value === 'number' && Number.isFinite(value)) {
      if (spec.type === 'integer') return String(value);
      const decimal = String(value);
      return (decimal.includes('e') ? decimal.replace(/e/i, 'd') : decimal + 'd0');
    }
    if (spec.type === 'enum' && spec.values.includes(value) && /^[a-z][a-z0-9-]*$/i.test(value))
      return ':' + value;
    throw new Error('Parameter tidak dapat diekspor: ' + key);
  }

  function exportRunScript(params, schema = defaultSchema) {
    for (const [key, value] of Object.entries(params || {})) {
      const spec = schema && schema[key];
      if (!spec) continue;
      if ((typeof value === 'number' && !Number.isFinite(value)) ||
          (spec.type === 'enum' && !spec.values.includes(value)))
        throw new Error('Parameter tidak dapat diekspor: ' + key);
    }
    const config = configApi.normalize(params || {}, schema);
    if (config.scenario === 'joss-bay' && config.constitutiveModel === 'custom')
      throw new Error('Joss Bay requires its dedicated reference material.');
    const lines = [];
    for (const [key, value] of Object.entries(config)) {
      if (!/^[A-Za-z][A-Za-z0-9]*$/.test(key)) throw new Error('Invalid schema key: ' + key);
      lines.push('  (setf (gethash "' + key + '" config) ' + lispValue(value, schema[key], key) + ')');
    }
    return `;;;; Exported from CL-MPM Studio. Requires the CL-MPM / Quicklisp environment.
;;;; Run from repository root; keep custom-model.lisp beside this script
;;;; when constitutiveModel = custom. No arbitrary source is loaded otherwise.
(in-package :cl-user)
(ql:quickload :cl-mpm-studio)
(let ((config (cl-mpm-studio:load-config)))
${lines.join('\n')}
  (when (eq (gethash "constitutiveModel" config) :custom)
    (cl-mpm-studio:load-custom-model (merge-pathnames "custom-model.lisp"
                           (uiop:pathname-directory-pathname *load-truename*))))
  (cl-mpm-studio:run config (uiop:ensure-directory-pathname #p"output/studio-export/")))
`;
  }

  return { MAX_SOURCE_BYTES, TEMPLATES, validateSource, exportRunScript };
}));
