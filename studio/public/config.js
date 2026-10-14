'use strict';
// One normalizer for HTTP runs and browser exports; ranges/defaults come from schema.json.
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.StudioConfig = api;
}(typeof window !== 'undefined' ? window : null, function () {
  const DECIMAL = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i;

  function normalize(input, schema) {
    if (!input || typeof input !== 'object' || Array.isArray(input))
      throw new TypeError('Simulation parameters must be a JSON object.');
    if (!schema || typeof schema !== 'object') throw new TypeError('Parameter schema is unavailable.');
    const config = {};
    for (const [key, spec] of Object.entries(schema)) {
      const value = Object.prototype.hasOwnProperty.call(input, key) ? input[key] : undefined;
      switch (spec.type) {
        case 'number':
        case 'integer': {
          const numeric = typeof value === 'number' ||
            (typeof value === 'string' && DECIMAL.test(value.trim()));
          let n = numeric ? Number(value) : NaN;
          if (!Number.isFinite(n)) n = spec.default;
          n = Math.min(spec.max, Math.max(spec.min, n));
          config[key] = spec.type === 'integer' ? Math.round(n) : n;
          break;
        }
        case 'boolean':
          config[key] = value === true || value === 'true' ? true :
            value === false || value === 'false' || value === null ? false : spec.default;
          break;
        case 'enum':
          config[key] = spec.values.includes(value) ? value : spec.default;
          break;
        default:
          throw new TypeError('Unknown schema type for ' + key);
      }
    }
    return config;
  }
  return { normalize };
}));
