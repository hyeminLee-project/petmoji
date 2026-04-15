"""SSE 기반 이모지 생성 스트리밍 엔드포인트"""

import json
import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.analyzer import analyze_pet_photo
from app.services.generator import EMOTIONS, PROVIDERS, _build_character_prompt
from app.utils.upload import MAX_PROMPT_LENGTH, read_and_validate_image

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


def _sse_event(event: str, data: dict) -> str:
    """SSE 포맷으로 이벤트 직렬화"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/generate/stream")
@limiter.limit("10/minute")
async def generate_emojis_stream(
    request: Request,
    file: UploadFile = File(...),
    style: str = Form("2d"),
    emoji_count: int = Form(8),
    provider: str = Form("gemini"),
    analyzer: str = Form("gemini"),
    custom_prompt: str = Form(""),
):
    """SSE 스트리밍으로 이모지 생성 진행 상황을 실시간 전송"""
    # 입력 검증
    if style not in ("2d", "3d"):
        raise HTTPException(status_code=400, detail="style은 '2d' 또는 '3d'만 가능합니다")
    if provider not in ("openai", "gemini"):
        raise HTTPException(
            status_code=400, detail="provider는 'openai' 또는 'gemini'만 가능합니다"
        )
    if analyzer not in ("anthropic", "gemini"):
        raise HTTPException(
            status_code=400, detail="analyzer는 'anthropic' 또는 'gemini'만 가능합니다"
        )
    if not 1 <= emoji_count <= 16:
        raise HTTPException(status_code=400, detail="emoji_count는 1~16 사이여야 합니다")
    if len(custom_prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"프롬프트는 {MAX_PROMPT_LENGTH}자 이하여야 합니다"
        )

    image_bytes, content_type = await read_and_validate_image(file)

    async def event_generator():
        # Step 1: 사진 분석
        yield _sse_event(
            "progress",
            {
                "step": "analyzing",
                "message": "반려동물 특징을 분석하고 있어요...",
                "progress": 0.05,
            },
        )

        try:
            pet_features = await analyze_pet_photo(image_bytes, content_type, analyzer)
        except Exception:
            logger.exception("Pet analysis failed during stream")
            yield _sse_event("error", {"message": "사진 분석에 실패했습니다"})
            return

        yield _sse_event(
            "progress",
            {
                "step": "analyzed",
                "message": "분석 완료! 이모지 생성을 시작합니다",
                "progress": 0.1,
                "pet_features": pet_features.model_dump(),
            },
        )

        # Step 2: 이모지 생성
        generate_fn = PROVIDERS[provider]
        base_prompt = _build_character_prompt(pet_features, style, custom_prompt)
        emotions_to_generate = EMOTIONS[:emoji_count]
        emojis = []

        for i, (emotion, description) in enumerate(emotions_to_generate):
            progress = 0.1 + (0.9 * (i / emoji_count))
            yield _sse_event(
                "progress",
                {
                    "step": "generating",
                    "message": f"이모지 생성 중 ({i + 1}/{emoji_count})...",
                    "progress": round(progress, 2),
                    "current": i + 1,
                    "total": emoji_count,
                },
            )

            prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

            try:
                image_url = await generate_fn(prompt)
            except Exception:
                logger.exception("Emoji generation failed for %s", emotion)
                yield _sse_event("error", {"message": f"이모지 생성 실패: {emotion}"})
                return

            emoji_data = {"emotion": emotion, "image_url": image_url}
            emojis.append(emoji_data)

            yield _sse_event(
                "emoji",
                {
                    "emotion": emotion,
                    "image_url": image_url,
                    "index": i,
                    "total": emoji_count,
                },
            )

        # 완료
        yield _sse_event(
            "complete",
            {
                "pet_features": pet_features.model_dump(),
                "emojis": emojis,
            },
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
