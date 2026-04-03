"""공유 검증 유틸리티."""

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


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
