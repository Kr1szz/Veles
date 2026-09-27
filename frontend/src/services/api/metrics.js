import { requestJson } from './client';

export async function getMetrics() {
  return requestJson('/metrics', { credentials: 'same-origin' }, 'Failed to fetch metrics');
}
