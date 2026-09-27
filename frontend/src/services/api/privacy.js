import { requestJson } from './client';

export async function getAuditLedger(limit = 50) {
  return requestJson(`/dpdpa/audit-ledger?limit=${limit}`, {}, 'Failed to fetch audit ledger');
}

export async function verifyAuditChain() {
  return requestJson('/dpdpa/audit-ledger/verify', { method: 'POST' }, 'Audit chain verification request failed');
}

export async function getConsents() {
  return requestJson('/dpdpa/consents', {}, 'Failed to fetch consent ledger');
}

export async function requestErasure(identifier, reason) {
  return requestJson('/dpdpa/erasure', { method: 'POST', body: { identifier, reason } }, 'Erasure request failed');
}
