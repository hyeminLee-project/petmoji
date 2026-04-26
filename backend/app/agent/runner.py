"""Agent 루프 — anthropic SDK tool_use 기반 자율 이모지 생성."""

import base64
import logging
from collections.abc import Callable
from typing import Any

import anthropic

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOLS, execute_tool
from app.services.generator import _sanitize_custom_prompt

logger = logging.getLogger(__name__)

MAX_TURNS = 10


async def run_agent(
    image_bytes: bytes,
    content_type: str,
    user_prompt: str,
    on_event: Callable[[str, dict], Any] | None = None,
    max_turns: int = MAX_TURNS,
) -> dict:
    """사진 + 자연어 프롬프트로 Agent 루프를 실행한다.

    Args:
        image_bytes: 업로드된 이미지 바이트
        content_type: 이미지 MIME 타입 (image/jpeg, image/png 등)
        user_prompt: 사용자 자연어 요청
        on_event: SSE 이벤트 콜백. (event_type, data) 형식.
        max_turns: 최대 턴 수 (무한 루프 방지)

    Returns:
        {"summary": str, "emojis": list, "converted": list | None}
    """
    sanitized = _sanitize_custom_prompt(user_prompt)
    if not sanitized:
        return {"error": "유효하지 않은 프롬프트입니다"}

    client = anthropic.AsyncAnthropic()
    context: dict[str, Any] = {
        "image_bytes": image_bytes,
        "content_type": content_type,
    }

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    messages: list[dict] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": content_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": sanitized},
            ],
        }
    ]

    async def emit(event_type: str, data: dict) -> None:
        if on_event:
            await on_event(event_type, data)

    for turn in range(max_turns):
        logger.info("Agent turn %d/%d", turn + 1, max_turns)

        response = await client.messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Claude가 최종 응답을 반환하면 종료
        if response.stop_reason == "end_turn":
            text = ""
            for block in response.content:
                if block.type == "text":
                    text += block.text
            return {
                "summary": text,
                "emojis": [e.model_dump() for e in context.get("emojis", [])],
                "converted": (
                    [c.model_dump() for c in context["converted"]]
                    if "converted" in context
                    else None
                ),
            }

        # tool_use 블록 처리
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            logger.warning("No tool_use blocks and stop_reason=%s", response.stop_reason)
            break

        # assistant 메시지를 히스토리에 추가
        messages.append({"role": "assistant", "content": response.content})

        # 각 tool_use 실행 후 결과를 모아서 한 번에 추가
        tool_results = []
        for block in tool_use_blocks:
            await emit(
                "tool_call",
                {
                    "tool": block.name,
                    "input": block.input,
                    "turn": turn + 1,
                },
            )

            try:
                result_str = await execute_tool(block.name, block.input, context)
                is_error = False
            except Exception as e:
                logger.exception("Tool execution failed: %s", block.name)
                result_str = f"도구 실행 실패: {e}"
                is_error = True

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                    **({"is_error": True} if is_error else {}),
                }
            )

            await emit(
                "tool_result",
                {
                    "tool": block.name,
                    "success": not is_error,
                    "turn": turn + 1,
                },
            )

        messages.append({"role": "user", "content": tool_results})

    return {
        "error": f"최대 턴({max_turns})을 초과했습니다",
        "emojis": [e.model_dump() for e in context.get("emojis", [])],
    }
