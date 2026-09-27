import { requestJson } from './client';

export async function getRules() {
  return requestJson('/rules', {}, 'Failed to fetch rules');
}
