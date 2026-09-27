import { requestJson } from './client';

async function submitVerification(path, payload, fallbackMessage) {
  const startedAt = performance.now();
  let clientLatencyMs = 0;
  const result = await requestJson(
    path,
    { method: 'POST', body: payload },
    fallbackMessage,
    () => { clientLatencyMs = performance.now() - startedAt; },
  );
  result.client_measured_latency_ms = Math.round(clientLatencyMs * 10) / 10;
  return result;
}

export function verifyKYC(payload) {
  return submitVerification('/verify/kyc', payload, 'KYC verification failed');
}

export function verifyTransaction(payload) {
  return submitVerification('/verify/transaction', payload, 'Transaction verification failed');
}

export async function getVerificationRecords(limit = 20, offset = 0, decision = '', entityType = '') {
  const params = new URLSearchParams({ limit, offset });
  if (decision) params.set('decision', decision);
  if (entityType) params.set('entity_type', entityType);
  return requestJson(`/verify/records?${params}`, {}, 'Failed to fetch records');
}
