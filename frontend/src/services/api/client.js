const API_BASE = '/api/v1';

export function defaultHeaders() {
  return { 'Content-Type': 'application/json' };
}

export async function requestJson(path, options = {}, fallbackMessage = 'Request failed', onResponse) {
  const { body, ...fetchOptions } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers: fetchOptions.headers || defaultHeaders(),
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  onResponse?.(response);

  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      // Some endpoints return an empty or non-JSON error response.
    }
    throw new Error(detail || fallbackMessage);
  }

  return response.json();
}

export { API_BASE };
