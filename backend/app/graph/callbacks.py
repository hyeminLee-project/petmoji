"""SSE 콜백 — LangGraph 노드에서 프론트엔드로 이벤트 전송."""

import asyncio
import json
from collections.abc import AsyncGenerator


class SSECallback:
    """비동기 큐 기반 SSE 이벤트 스트리머."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()

    async def emit(self, event: str, data: dict):
        """SSE 이벤트 전송."""
        await self.queue.put((event, data))

    async def done(self):
        """스트림 종료 시그널."""
        await self.queue.put(None)

    async def stream(self) -> AsyncGenerator[str, None]:
        """SSE 포맷 문자열 생성."""
        while True:
            item = await self.queue.get()
            if item is None:
                break
            event, data = item
            yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
