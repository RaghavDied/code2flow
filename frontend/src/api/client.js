const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const TIMEOUT_MS = 15000;

const MOCK_LOADERS = {
  '/tokens': () => import('../mocks/tokens_ok.json'),
  '/ast': () => import('../mocks/ast_ok.json'),
  '/generate': () => import('../mocks/generate_ok.json'),
  '/optimize': () => import('../mocks/optimize_ok.json'),
};

/** Build an envelope-shaped error so the UI handles it like a compile error. */
function errorEnvelope(message) {
  return {
    ok: false,
    errors: [{ phase: 'frontend', severity: 'error', message, line: 0, col: 0 }],
    warnings: [],
    data: null,
  };
}

/** Guarantee the envelope always has ok/errors/warnings/data. */
function normalise(json) {
  if (!json || typeof json !== 'object') {
    return errorEnvelope('Backend returned an unexpected response');
  }
  const errors = Array.isArray(json.errors) ? json.errors : [];
  return {
    ok: errors.length === 0 && json.ok !== false,
    errors,
    warnings: Array.isArray(json.warnings) ? json.warnings : [],
    data: errors.length === 0 ? json.data ?? null : null,
  };
}

/** Load a mock response. Only used when VITE_USE_MOCKS=true. */
async function loadMock(endpoint) {
  const loader = MOCK_LOADERS[endpoint];
  if (!loader) {
    return errorEnvelope(`No mock available for ${endpoint}`);
  }
  const mod = await loader();
  console.warn(`[client] MOCK data used for ${endpoint}. Your code was NOT compiled.`);
  return normalise(mod.default);
}

/**
 * POST to the backend and return the standard envelope:
 * { ok, errors, warnings, data }
 */
async function postRequest(endpoint, code) {
  if (USE_MOCKS) return loadMock(endpoint);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ language: 'c', code }),
      signal: controller.signal,
    });

    if (!response.ok) {
      return errorEnvelope(`Backend error ${response.status} on ${endpoint}`);
    }

    let json;
    try {
      json = await response.json();
    } catch {
      return errorEnvelope(`Backend sent invalid JSON on ${endpoint}`);
    }
    return normalise(json);
  } catch (error) {
    console.error(`API error on ${endpoint}:`, error);
    const message =
      error.name === 'AbortError'
        ? `Backend timed out after ${TIMEOUT_MS / 1000}s`
        : `Cannot reach backend at ${API_URL}. Is uvicorn running?`;
    return errorEnvelope(message);
  } finally {
    clearTimeout(timer);
  }
}

export const fetchTokens = (code) => postRequest('/tokens', code);
export const fetchAst = (code) => postRequest('/ast', code);
export const fetchGenerate = (code) => postRequest('/generate', code);
export const fetchOptimize = (code) => postRequest('/optimize', code);
