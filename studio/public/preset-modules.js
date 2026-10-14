'use strict';
/**
 * Versioned, declarative Lisp-like preset interchange. This is intentionally
 * NOT a Lisp reader and does not call load/eval or execute imported code.
 */
(function (root, factory) {
  const node = typeof module === 'object' && module.exports;
  const api = factory(node ? require('./config.js') : root.StudioConfig,
    node ? require('../schema.json').parameters : undefined);
  if (node) module.exports = api;
  if (root) root.StudioPresetModules = api;
}(typeof window !== 'undefined' ? window : null, function (configApi, defaultSchema) {
  const VERSION = 1;
  const MAX_FILE_BYTES = 128 * 1024;
  const MAX_SOURCE_BYTES = 32 * 1024;
  const GROUPS = Object.freeze({
    geometry: ['shelfHeight', 'shelfAspect', 'cliffSlope', 'undercut',
      'notchHeight', 'notchDepth', 'notchShape', 'notchTipFraction', 'soilBoundary'],
    materials: ['density', 'E', 'nu', 'frictionAngle', 'cohesion',
      'dilatancyAngle', 'nonlocalLength', 'ductility', 'initiationStress',
      'delayTime', 'enablePlasticity', 'enableDamage', 'constitutiveModel'],
    solver: ['meshSize', 'mpsPerCell', 'maxSteps', 'substeps', 'workers'],
    output: ['plotMode'],
    'constitutive-source': [],
  });
  const IDS = Object.freeze(Object.keys(GROUPS));
  const NUMERIC = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[dDeE][+-]?\d+)?$/;

  function schemaRequired(schema) {
    const result = schema === undefined ? defaultSchema : schema;
    if (!result || typeof result !== 'object') throw new Error('Preset schema is required.');
    for (const keys of Object.values(GROUPS))
      for (const key of keys) if (!result[key]) throw new Error('Schema missing: ' + key);
    return result;
  }
  function byteSize(s) { return new TextEncoder().encode(s).length; }
  function checkSource(s) {
    if (typeof s !== 'string' || s.includes('\0') || byteSize(s) > MAX_SOURCE_BYTES)
      throw new Error('Model source must be text up to 32 KiB, with no NUL bytes.');
  }
  function encodeSource(s) {
    return Array.from(new TextEncoder().encode(s), b => b.toString(16).padStart(2, '0')).join('');
  }
  function decodeSource(hex) {
    if (!/^(?:[0-9a-f]{2})*$/.test(hex) || hex.length > 2 * MAX_SOURCE_BYTES)
      throw new Error('Invalid source encoding.');
    const bytes = new Uint8Array(hex.length / 2);
    for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
    const s = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
    checkSource(s);
    return s;
  }
  function serialize(value, spec) {
    if (spec.type === 'boolean') return value ? 't' : 'nil';
    if (spec.type === 'enum') return ':' + value;
    if (spec.type === 'integer') return String(value);
    const n = String(value);
    return n.replace(/e/i, 'd') + (n.includes('e') ? '' : 'd0');
  }
  function serializeModule(id, config, source, schema) {
    if (!IDS.includes(id)) throw new Error('Unsupported module: ' + id);
    const lines = ['(studio-module :version 1 :id :' + id + ')'];
    if (id === 'constitutive-source') {
      checkSource(source);
      lines.push('(source-hex "' + encodeSource(source) + '")');
    } else {
      for (const key of GROUPS[id])
        lines.push('(param :' + key + ' ' + serialize(config[key], schema[key]) + ')');
    }
    lines.push('(end-module)');
    return lines.join('\n');
  }
  function exportModules(ids, input, source = '', schema) {
    const specs = schemaRequired(schema);
    if (!Array.isArray(ids) || ids.length === 0 || new Set(ids).size !== ids.length ||
        ids.some(id => !IDS.includes(id)))
      throw new Error('Choose unique supported module IDs.');
    const config = configApi.normalize(input || {}, specs);
    const parts = ids.map(id => serializeModule(id, config, source, specs));
    const prefix = ';;;; CL-MPM Studio declarative preset (INERT; not executable)\n';
    if (parts.length === 1) return prefix + parts[0] + '\n';
    return prefix + '(studio-preset :version 1)\n' +
      parts.join('\n\n') + '\n(end-preset)\n';
  }
  function exportFullPreset(input, source = '', schema) {
    return exportModules(IDS, input, source, schema);
  }
  function parseValue(token, spec, key) {
    if (spec.type === 'boolean') {
      if (token !== 't' && token !== 'nil') throw new Error('Invalid boolean: ' + key);
      return token === 't';
    }
    if (spec.type === 'enum') {
      if (!token.startsWith(':') || !spec.values.includes(token.slice(1)))
        throw new Error('Invalid enum: ' + key);
      return token.slice(1);
    }
    if (!NUMERIC.test(token)) throw new Error('Invalid numeric value: ' + key);
    const n = Number(token.replace(/[dD]/g, 'e'));
    if (!Number.isFinite(n) || (spec.type === 'integer' && !Number.isInteger(n)) ||
        n < spec.min || n > spec.max)
      throw new Error('Out of range: ' + key);
    return n;
  }
  function inspectImport(text, schema) {
    const specs = schemaRequired(schema);
    if (typeof text !== 'string' || byteSize(text) > MAX_FILE_BYTES)
      throw new Error('Preset file must be text up to 128 KiB.');
    const lines = text.split(/\r?\n/).map(s => s.trim()).filter(s => s && !s.startsWith(';;;;'));
    if (!lines.length) throw new Error('Empty preset.');
    const fullHeader = lines[0] === '(studio-preset :version 1)';
    if (lines[0].startsWith('(studio-preset') && !fullHeader)
      throw new Error('Unsupported preset version.');
    let i = fullHeader ? 1 : 0;
    const modules = [];
    let finished = false;
    while (i < lines.length) {
      if (!fullHeader && modules.length) throw new Error('Trailing expressions are not supported.');
      if (fullHeader && lines[i] === '(end-preset)') {
        finished = true;
        i++;
        break;
      }
      const m = /^\(studio-module :version 1 :id :([a-z-]+)\)$/.exec(lines[i++]);
      if (!m || !IDS.includes(m[1])) throw new Error('Unsupported module or Lisp expression.');
      const id = m[1];
      if (modules.some(item => item.id === id)) throw new Error('Duplicate module: ' + id);
      const fields = Object.create(null);
      let source;
      let count = 0;
      while (i < lines.length && lines[i] !== '(end-module)') {
        const line = lines[i++];
        if (id === 'constitutive-source') {
          const s = /^\(source-hex "([0-9a-f]*)"\)$/.exec(line);
          if (!s || source !== undefined) throw new Error('Invalid constitutive source form.');
          source = decodeSource(s[1]);
        } else {
          const p = /^\(param :([A-Za-z][A-Za-z0-9]*) ([^\s()]+)\)$/.exec(line);
          if (!p || !GROUPS[id].includes(p[1]) ||
              Object.prototype.hasOwnProperty.call(fields, p[1]))
            throw new Error('Unknown, duplicate, or executable Lisp form in ' + id);
          fields[p[1]] = parseValue(p[2], specs[p[1]], p[1]);
        }
        if (++count > 60) throw new Error('Too many module fields.');
      }
      if (lines[i++] !== '(end-module)') throw new Error('Unclosed module.');
      if (id === 'constitutive-source' && source === undefined)
        throw new Error('Missing constitutive source.');
      if (id !== 'constitutive-source' && count === 0)
        throw new Error('Empty module.');
      modules.push(id === 'constitutive-source' ? { id, source } : { id, params: fields });
    }
    if (fullHeader && !finished) throw new Error('Unclosed preset.');
    if (i !== lines.length || modules.length === 0 || (!fullHeader && modules.length !== 1))
      throw new Error('Trailing or invalid preset forms.');
    const ids = modules.map(x => x.id);
    return { version: VERSION, modules, ids, complete: IDS.every(id => ids.includes(id)) };
  }
  function previewImport(current, currentSource, text, mode = 'merge', schema) {
    const specs = schemaRequired(schema);
    if (mode !== 'merge' && mode !== 'replace')
      throw new Error('Import mode must be merge or replace.');
    const parsed = inspectImport(text, specs);
    const before = configApi.normalize(current || {}, specs);
    const nextConfig = { ...before };
    checkSource(currentSource);
    let nextSource = currentSource;
    for (const module of parsed.modules) {
      if (module.id === 'constitutive-source') {
        nextSource = module.source; // whole source is replaced, never merged as lines.
      } else {
        if (mode === 'replace')
          for (const key of GROUPS[module.id]) nextConfig[key] = specs[key].default;
        Object.assign(nextConfig, module.params);
      }
    }
    if (nextConfig.constitutiveModel === 'custom' && !nextSource.trim())
      throw new Error('Custom model requires source. Import constitutive-source too.');
    const changes = [];
    for (const key of Object.keys(nextConfig))
      if (!Object.is(before[key], nextConfig[key]))
        changes.push({ key, before: before[key], after: nextConfig[key] });
    if (nextSource !== currentSource)
      changes.push({ key: 'constitutive-source',
        before: byteSize(currentSource) + ' bytes',
        after: byteSize(nextSource) + ' bytes' });
    return { ...parsed, mode, changes, nextConfig, nextSource };
  }
  return { VERSION, GROUPS, IDS, MAX_FILE_BYTES, MAX_SOURCE_BYTES,
    exportModules, exportFullPreset, inspectImport, previewImport };
}));
