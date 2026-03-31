import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.converters import CONVERTERS
from app.models.schemas import ConvertResponse, EmojiResult

logger = logging.getLogger(__name__)

router = APIRouter()

AVAILABLE_FORMATS = list(CONVERTERS.keys())


# base64 이미지 URL 최대 크기: 10MB (base64 인코딩 오버헤드 포함)
MAX_IMAGE_URL_LENGTH = 14 * 1024 * 1024
MAX_EMOJIS_PER_REQUEST = 16


class ConvertRequest(BaseModel):
    emojis: list[EmojiResult]
    format: str  # kakao, imessage, sticker, gif, wallpaper


@router.get("/formats")
async def list_formats():
    """List available conversion formats."""
    return {
        "formats": [
            {"id": "kakao", "name": "카카오톡 이모티콘", "size": "360x360", "limit": "150KB"},
            {
                "id": "kakao_large_square",
                "name": "카카오 큰이모티콘 (정사각)",
                "size": "540x540",
                "limit": "1MB",
            },
            {
                "id": "kakao_large_wide",
                "name": "카카오 큰이모티콘 (가로)",
                "size": "540x300",
                "limit": "1MB",
            },
            {
                "id": "kakao_large_tall",
                "name": "카카오 큰이모티콘 (세로)",
                "size": "300x540",
                "limit": "1MB",
            },
            {"id": "imessage", "name": "iMessage 스티커", "size": "408x408"},
            {"id": "sticker", "name": "투명 스티커 PNG", "size": "512x512"},
            {"id": "gif", "name": "움직이는 GIF", "size": "256x256"},
            {"id": "wallpaper", "name": "폰 배경화면", "size": "1170x2532"},
        ]
    }


@router.post("/convert", response_model=ConvertResponse)
async def convert_emojis(request: ConvertRequest):
    """Convert generated emojis to a specific platform format."""
    if request.format not in CONVERTERS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 포맷: {request.format}. 가능: {AVAILABLE_FORMATS}",
        )

    if not request.emojis:
        raise HTTPException(status_code=400, detail="변환할 이모지가 없습니다")

    if len(request.emojis) > MAX_EMOJIS_PER_REQUEST:
        raise HTTPException(
            status_code=400, detail=f"한 번에 최대 {MAX_EMOJIS_PER_REQUEST}개까지 변환 가능합니다"
        )

    for emoji in request.emojis:
        if len(emoji.image_url) > MAX_IMAGE_URL_LENGTH:
            raise HTTPException(status_code=400, detail="이미지 데이터가 너무 큽니다 (최대 10MB)")

    try:
        converter = CONVERTERS[request.format]
        converted = converter(request.emojis)
    except Exception as e:
        logger.error("Conversion failed (%s): %s", request.format, e)
        raise HTTPException(status_code=500, detail="포맷 변환 중 오류가 발생했습니다") from e

    return ConvertResponse(format=request.format, emojis=converted)
