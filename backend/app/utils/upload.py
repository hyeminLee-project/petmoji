"""파일 업로드 공통 유틸리티 — 매직 바이트 검증 + 청크 읽기."""

from fastapi import HTTPException, UploadFile

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PROMPT_LENGTH = 500
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}


def detect_content_type(data: bytes) -> str | None:
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


async def read_and_validate_image(file: UploadFile) -> tuple[bytes, str]:
    """파일 업로드를 읽고 크기 + 매직 바이트를 검증한다.

    Returns:
        (image_bytes, content_type) 튜플
    Raises:
        HTTPException: 검증 실패 시
    """
    # Content-Length 사전 체크 (전체 로드 전 거부)
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다")

    # 청크 단위 읽기로 메모리 보호
    chunks: list[bytes] = []
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
    detected_type = detect_content_type(image_bytes)
    if not detected_type or detected_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다")

    return image_bytes, detected_type
