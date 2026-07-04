"""움직이는 이모지 생성 엔드포인트 (Runway, 프리미엄 전용)."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.converters.video import video_to_pingpong_gif
from app.models.schemas import ConvertedEmoji, EmojiResult
from app.models.tiers import TierType
from app.routers.convert import MAX_IMAGE_URL_LENGTH
from app.services.animator import generate_motion_video, is_configured

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


class AnimateRequest(BaseModel):
    emoji: EmojiResult
    tier: TierType = "free"


@router.post("/animate", response_model=ConvertedEmoji)
@limiter.limit("3/minute")
async def animate_emoji(request: Request, body: AnimateRequest):
    """정지 이모지 하나를 AI 영상 모델로 애니메이션화하여 GIF 반환."""
    if body.tier == "free":
        raise HTTPException(
            status_code=403, detail="움직이는 이모지는 프리미엄 티어 전용 기능입니다"
        )
    if not is_configured():
        raise HTTPException(
            status_code=503, detail="움직이는 이모지 기능이 아직 준비되지 않았습니다"
        )
    if len(body.emoji.image_url) > MAX_IMAGE_URL_LENGTH:
        raise HTTPException(status_code=400, detail="이미지 데이터가 너무 큽니다 (최대 10MB)")

    try:
        video_bytes = await generate_motion_video(body.emoji.image_url, body.emoji.emotion)
    except Exception as e:
        logger.exception("Motion video generation failed")
        raise HTTPException(status_code=502, detail="영상 생성에 실패했습니다") from e

    try:
        gif_url = await asyncio.to_thread(video_to_pingpong_gif, video_bytes, body.emoji.caption)
    except Exception as e:
        logger.exception("Video to GIF conversion failed")
        raise HTTPException(status_code=500, detail="GIF 변환 중 오류가 발생했습니다") from e

    return ConvertedEmoji(
        emotion=body.emoji.emotion,
        image_url=gif_url,
        format="animated",
        width=360,
        height=360,
    )
