"""In-memory event bus for live agent progress (SSE).

A simple asyncio pub/sub keyed by task_id. No external broker is used —
consistent with the sovereign/local-first requirement.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._queues: dict[str, set[asyncio.Queue]] = {}

    def _key(self, task_id: int | str) -> str:
        return f"task:{task_id}"

    def subscribe(self, task_id: int | str) -> asyncio.Queue:
        key = self._key(task_id)
        q: asyncio.Queue = asyncio.Queue()
        if key not in self._queues:
            self._queues[key] = set()
        self._queues[key].add(q)
        return q

    def unsubscribe(self, task_id: int | str, q: asyncio.Queue) -> None:
        key = self._key(task_id)
        subs = self._queues.get(key)
        if subs:
            subs.discard(q)
            if not subs:
                self._queues.pop(key, None)

    async def publish(self, task_id: int | str, event: dict[str, Any]) -> None:
        key = self._key(task_id)
        subs = self._queues.get(key)
        if not subs:
            return
        message = {"id": str(uuid.uuid4()), **event}
        for q in list(subs):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass

    async def subscribe_stream(self, task_id: int | str):
        """Async generator of SSE-formatted events for a task."""
        q = self.subscribe(task_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield _sse(event)
                except TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            self.unsubscribe(task_id, q)


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
