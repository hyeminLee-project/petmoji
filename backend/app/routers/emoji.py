import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import GenerateResponse
from app.models.tiers import TIER_CONFIG, TierType
from app.services.analyzer import analyze_pet_photo
from app.services.generator import generate_emoji_set
from app.utils.upload import MAX_PROMPT_LENGTH, read_and_validate_image

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit("10/minute")
async def generate_emojis(
    request: Request,
    file: UploadFile = File(...),
    style: str = Form("2d"),
    emoji_count: int = Form(8),
    provider: str = Form("gemini"),
    analyzer: str = Form("gemini"),
    custom_prompt: str = Form(""),
    tier: TierType = Form("free"),
):
    """Upload a pet photo and generate a personalized emoji set."""
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

    max_emotions = TIER_CONFIG[tier]["max_emotions"]
    if not 1 <= emoji_count <= max_emotions:
        raise HTTPException(
            status_code=400,
            detail=f"emoji_count는 1~{max_emotions} 사이여야 합니다 ({tier} 티어)",
        )

    if len(custom_prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"프롬프트는 {MAX_PROMPT_LENGTH}자 이하여야 합니다"
        )

    image_bytes, content_type = await read_and_validate_image(file)

    try:
        # Step 1: Analyze pet features
        pet_features = await analyze_pet_photo(image_bytes, content_type, analyzer)
    except ValueError as e:
        logger.error("Pet analysis failed: %s", e)
        raise HTTPException(status_code=422, detail="사진 분석에 실패했습니다") from e
    except Exception as e:
        logger.exception("Unexpected analysis error")
        raise HTTPException(status_code=500, detail="사진 분석 중 오류가 발생했습니다") from e

    try:
        # Step 2: Generate emoji set with GPT-4o
        emojis = await generate_emoji_set(
            pet_features,
            style,
            emoji_count,
            provider,
            custom_prompt,
        )
    except Exception as e:
        logger.exception("Emoji generation failed")
        raise HTTPException(status_code=500, detail="이모지 생성 중 오류가 발생했습니다") from e

    return GenerateResponse(pet_features=pet_features, emojis=emojis)
