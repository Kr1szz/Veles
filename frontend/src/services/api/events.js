import { API_BASE } from './client';

export function connectEventStream(onEvent, onStatus) {
  const eventSource = new EventSource(`${API_BASE}/events/stream`, { withCredentials: true });
  eventSource.onopen = () => onStatus?.('connected');
  eventSource.onmessage = (event) => {
    try {
      onEvent(JSON.parse(event.data));
    } catch {
      onStatus?.('reconnecting');
    }
  };
  // Leave the source open so the browser can retry after transient failures.
  eventSource.onerror = () => onStatus?.('reconnecting');
  return () => eventSource.close();
}

export async function getRecentEvents() {
  const response = await fetch(`${API_BASE}/events/recent`, { credentials: 'same-origin' });
  if (!response.ok) return [];
  return response.json();
}
