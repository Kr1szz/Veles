import { requestJson } from './client';

export async function getReviewQueue(limit = 50) {
  return requestJson(`/reviews/queue?limit=${limit}`, { credentials: 'same-origin' }, 'Failed to fetch review queue');
}

export async function overrideDecision(verificationId, overrideDecision, reviewNotes) {
  return requestJson(`/reviews/${encodeURIComponent(verificationId)}/override`, {
    method: 'POST',
    body: { override_decision: overrideDecision, review_notes: reviewNotes },
  }, 'Decision override failed');
}
