const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Common POST fetch wrapper returning the standard API response envelope:
 * { ok, errors, warnings, data }
 */
async function postRequest(endpoint, code) {
  try {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ language: 'c', code }),
    });
    return await response.json();
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    return {
      ok: false,
      errors: [
        {
          phase: 'frontend',
          severity: 'error',
          message: error.message || 'Failed to connect to backend service',
          line: 0,
          col: 0,
        },
      ],
      warnings: [],
      data: null,
    };
  }
}

export const fetchTokens = (code) => postRequest('/tokens', code);
export const fetchAst = (code) => postRequest('/ast', code);
export const fetchGenerate = (code) => postRequest('/generate', code);
export const fetchOptimize = (code) => postRequest('/optimize', code);