"""감정별 이모지 병렬 생성 스트리밍 코어.

무료 스트림(emoji_stream)과 위자드(wizard)가 공유하는 생성 루프.
이벤트 싱크(SSE yield / SSECallback)와 무관하게 (event, payload) 튜플을 산출하고,
각 라우터는 자신의 전송 방식으로 감싸기만 한다.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable

from app.models.schemas import PetFeatures
from app.services.caption import generate_captions
from app.services.generator import enhance_prompt_with_hermes, generation_semaphore

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str], Awaitable[str]]


async def fetch_captions_safe(
    emotions: list[tuple[str, str]],
    pet_features: dict | PetFeatures | None,
    provider: str,
) -> dict[str, str]:
    """캡션 일괄 생성. 실패하거나 특징 정보가 없으면 빈 딕셔너리로 계속 진행."""
    if not pet_features:
        return {}
    try:
        if isinstance(pet_features, dict):
            pet_features = PetFeatures(**pet_features)
        return await generate_captions(emotions, pet_features, provider)
    except Exception:
        logger.exception("Caption generation failed, continuing without captions")
        return {}


async def stream_emoji_generation(
    base_prompt: str,
    suffix: str,
    emotions: list[tuple[str, str]],
    generate_fn: GenerateFn,
    captions: dict[str, str],
    enhance_with_hermes: bool = False,
    progress_start: float = 0.0,
) -> AsyncIterator[tuple[str, dict]]:
    """감정별 이모지를 병렬 생성하며 이벤트를 완료 순서대로 산출.

    산출 이벤트:
    - ("progress", ...) / ("emoji", ...) — 이모지 하나 완료될 때마다
    - ("error", ...) — 생성 실패 시 남은 작업을 취소하고 종료
    - ("done", {"emojis": [...]}) — 원래 감정 순서로 정렬된 최종 목록

    Args:
        progress_start: 진행률 시작점 (선행 단계가 차지한 구간, 무료 스트림은 0.1)
    """
    total = len(emotions)
    emojis: list[dict] = []

    async def _generate_one(idx: int, emotion: str, description: str) -> tuple[int, str, str]:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
{suffix}"""
        if enhance_with_hermes:
            prompt = await enhance_prompt_with_hermes(prompt)
        async with generation_semaphore:
            image_url = await generate_fn(prompt)
        return idx, emotion, image_url

    tasks = [
        asyncio.ensure_future(_generate_one(i, emotion, desc))
        for i, (emotion, desc) in enumerate(emotions)
    ]

    for done_count, coro in enumerate(asyncio.as_completed(tasks), 1):
        try:
            idx, emotion, image_url = await coro
        except Exception:
            logger.exception("Emoji generation failed")
            for task in tasks:
                task.cancel()
            yield ("error", {"message": "이모지 생성 중 오류가 발생했습니다"})
            return

        emoji_data = {
            "emotion": emotion,
            "image_url": image_url,
            "caption": captions.get(emotion, ""),
        }
        emojis.append(emoji_data)

        progress = progress_start + (1.0 - progress_start) * (done_count / total)
        yield (
            "progress",
            {
                "step": "generating",
                "message": f"이모지 생성 중 ({done_count}/{total})...",
                "progress": round(progress, 2),
                "current": done_count,
                "total": total,
            },
        )
        yield ("emoji", {**emoji_data, "index": idx, "total": total})

    order = [emotion for emotion, _ in emotions]
    emojis.sort(key=lambda e: order.index(e["emotion"]))
    yield ("done", {"emojis": emojis})
