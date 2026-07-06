import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.converters import CONVERTERS, FORMAT_REGISTRY
from app.models.schemas import ConvertResponse, EmojiResult

logger = logging.getLogger(__name__)

router = APIRouter()

AVAILABLE_FORMATS = list(FORMAT_REGISTRY.keys())


# base64 이미지 URL 최대 크기: 10MB (base64 인코딩 오버헤드 포함)
MAX_IMAGE_URL_LENGTH = 14 * 1024 * 1024


class ConvertRequest(BaseModel):
    emojis: list[EmojiResult]
    format: str  # FORMAT_REGISTRY의 키


@router.get("/formats")
async def list_formats():
    """사용 가능한 변환 포맷 목록 (FORMAT_REGISTRY 기반)."""
    return {
        "formats": [
            {
                "id": format_id,
                "name": meta["name"],
                "icon": meta["icon"],
                "size": meta["size"],
                "limit": meta["limit"],
                "max_count": meta["max_count"],
                "description": meta["description"],
            }
            for format_id, meta in FORMAT_REGISTRY.items()
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

    max_count = FORMAT_REGISTRY[request.format]["max_count"]
    if len(request.emojis) > max_count:
        raise HTTPException(
            status_code=400,
            detail=f"{request.format} 포맷은 최대 {max_count}개까지 변환 가능합니다",
        )

    for emoji in request.emojis:
        if len(emoji.image_url) > MAX_IMAGE_URL_LENGTH:
            raise HTTPException(status_code=400, detail="이미지 데이터가 너무 큽니다 (최대 10MB)")

    try:
        converter = CONVERTERS[request.format]
        converted = converter(request.emojis)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Conversion failed (%s): %s", request.format, e)
        raise HTTPException(status_code=500, detail="포맷 변환 중 오류가 발생했습니다") from e

    return ConvertResponse(format=request.format, emojis=converted)
