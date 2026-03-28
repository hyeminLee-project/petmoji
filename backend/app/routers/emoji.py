import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.schemas import GenerateResponse
from app.services.analyzer import analyze_pet_photo
from app.services.generator import generate_emoji_set

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


@router.post("/generate", response_model=GenerateResponse)
async def generate_emojis(
    file: UploadFile = File(...),
    style: str = Form("2d"),
    emoji_count: int = Form(8),
    provider: str = Form("gemini"),
    analyzer: str = Form("gemini"),
    custom_prompt: str = Form(""),
):
    """Upload a pet photo and generate a personalized emoji set."""
    # 입력 검증
    if style not in ("2d", "3d"):
        raise HTTPException(status_code=400, detail="style은 '2d' 또는 '3d'만 가능합니다")

    if provider not in ("openai", "gemini"):
        raise HTTPException(status_code=400, detail="provider는 'openai' 또는 'gemini'만 가능합니다")

    if analyzer not in ("anthropic", "gemini"):
        raise HTTPException(status_code=400, detail="analyzer는 'anthropic' 또는 'gemini'만 가능합니다")

    if not 1 <= emoji_count <= 16:
        raise HTTPException(status_code=400, detail="emoji_count는 1~16 사이여야 합니다")

    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식: {content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다")

    if not image_bytes:
        raise HTTPException(status_code=400, detail="빈 파일입니다")

    try:
        # Step 1: Analyze pet features
        pet_features = await analyze_pet_photo(image_bytes, content_type, analyzer)
    except ValueError as e:
        logger.error("Pet analysis failed: %s", e)
        raise HTTPException(status_code=422, detail=f"사진 분석 실패: {e}") from e
    except Exception as e:
        logger.error("Unexpected analysis error: %s", e)
        raise HTTPException(status_code=500, detail="사진 분석 중 오류가 발생했습니다") from e

    try:
        # Step 2: Generate emoji set with GPT-4o
        emojis = await generate_emoji_set(pet_features, style, emoji_count, provider, custom_prompt)
    except Exception as e:
        logger.error("Emoji generation failed: %s", e)
        raise HTTPException(status_code=500, detail="이모지 생성 중 오류가 발생했습니다") from e

    return GenerateResponse(pet_features=pet_features, emojis=emojis)
