import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List

logger = logging.getLogger("aegis.services.events")


class EventBroadcaster:
    """
    In-memory async pub-sub event broadcaster for real-time frontend streaming (SSE).
    Queues verification events and broadcasts them to all connected analyst dashboards.
    """

    def __init__(self, max_history: int = 100):
        self.subscribers: List[asyncio.Queue] = []
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        async with self._lock:
            self.subscribers.append(q)
            # Replay recent history to newly connected dashboard
            for event in self._history[-10:]:
                await q.put(event)
        return q

    async def unsubscribe(self, q: asyncio.Queue):
        async with self._lock:
            if q in self.subscribers:
                self.subscribers.remove(q)

    async def broadcast(self, event: Dict[str, Any]):
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            dead_queues = []
            for q in self.subscribers:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead_queues.append(q)

            for q in dead_queues:
                if q in self.subscribers:
                    self.subscribers.remove(q)

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(reversed(self._history[-limit:]))


event_broadcaster = EventBroadcaster()
