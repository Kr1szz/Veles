import asyncio
import json
from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse
from aegis.services.event_stream import event_broadcaster

router = APIRouter(prefix="/events", tags=["Real-Time Event Stream"])


@router.get("/stream")
async def sse_event_stream(request: Request):
    """
    Server-Sent Events (SSE) stream broadcasting real-time KYC and transaction verifications.
    """
    queue = await event_broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                # Disconnect check
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # SSE keep-alive ping comment
                    yield ": ping\n\n"
        finally:
            await event_broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/recent")
def get_recent_events():
    """
    Polling fallback returning recent stream events.
    """
    return event_broadcaster.get_recent_events(limit=25)
