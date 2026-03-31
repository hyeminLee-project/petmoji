import logging

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import GenerateResponse
from app.services.analyzer import analyze_pet_photo
from app.services.generator import generate_emoji_set

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PROMPT_LENGTH = 500
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

# 매직 바이트로 실제 이미지 타입 검증
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # RIFF....WEBP
}


def _detect_content_type(data: bytes) -> str | None:
    """파일 매직 바이트로 실제 Content-Type 감지."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    # HEIC: ftyp box
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "image/heic"
    return None


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

    if not 1 <= emoji_count <= 16:
        raise HTTPException(status_code=400, detail="emoji_count는 1~16 사이여야 합니다")

    if len(custom_prompt) > MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=400, detail=f"프롬프트는 {MAX_PROMPT_LENGTH}자 이하여야 합니다"
        )

    # Content-Length 사전 체크 (전체 로드 전 거부)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다")

    # 청크 단위 읽기로 메모리 보호
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(64 * 1024)  # 64KB씩 읽기
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다")
        chunks.append(chunk)
    image_bytes = b"".join(chunks)

    if not image_bytes:
        raise HTTPException(status_code=400, detail="빈 파일입니다")

    # 매직 바이트로 실제 이미지 타입 검증
    detected_type = _detect_content_type(image_bytes)
    if not detected_type or detected_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다")
    content_type = detected_type

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
        emojis = await generate_emoji_set(pet_features, style, emoji_count, provider, custom_prompt)
    except Exception as e:
        logger.exception("Emoji generation failed")
        raise HTTPException(status_code=500, detail="이모지 생성 중 오류가 발생했습니다") from e

    return GenerateResponse(pet_features=pet_features, emojis=emojis)
