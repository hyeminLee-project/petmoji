"""Agent 모드 SSE 엔드포인트 — 자연어 + 사진으로 이모지 자율 생성."""

import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.agent.runner import run_agent
from app.utils.upload import MAX_PROMPT_LENGTH, read_and_validate_image

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/agent")


def _sse_event(event: str, data: dict) -> str:
    """SSE 포맷으로 이벤트 직렬화."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/generate")
@limiter.limit("5/minute")
async def agent_generate(
    request: Request,
    file: UploadFile = File(...),
    prompt: str = Form(...),
):
    """자연어 프롬프트 + 사진으로 Agent가 자율적으로 이모지를 생성한다.

    SSE 이벤트:
    - tool_call: Agent가 도구를 호출할 때
    - tool_result: 도구 실행 결과
    - complete: 최종 결과
    - error: 에러 발생 시
    """
    if not prompt.strip():
        raise HTTPException(status_code=400, detail="프롬프트를 입력해주세요")
    if len(prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"프롬프트는 {MAX_PROMPT_LENGTH}자 이하여야 합니다"
        )

    image_bytes, content_type = await read_and_validate_image(file)

    async def event_generator():
        events: list[str] = []

        async def on_event(event_type: str, data: dict) -> None:
            events.append(_sse_event(event_type, data))

        yield _sse_event("progress", {"message": "Agent가 작업을 시작합니다..."})

        try:
            result = await run_agent(
                image_bytes=image_bytes,
                content_type=content_type,
                user_prompt=prompt,
                on_event=on_event,
            )
        except Exception:
            logger.exception("Agent run failed")
            yield _sse_event("error", {"message": "Agent 실행 중 오류가 발생했습니다"})
            return

        for event in events:
            yield event

        if "error" in result:
            yield _sse_event("error", {"message": result["error"]})
        else:
            yield _sse_event("complete", result)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
