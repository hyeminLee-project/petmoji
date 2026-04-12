"""카카오톡 이모티콘 규격 변환기.

카카오 오픈스튜디오 공식 규격 (emoticonstudio.kakao.com):

멈춰있는 이모티콘:
- PNG 32bit(투명), 72dpi, RGB
- 360x360px, ≤150KB/개, 총 32개

움직이는 이모티콘:
- PNG 21개 + GIF 3개, 72dpi, RGB
- 360x360px, ≤650KB/개, 총 24개

큰 이모티콘:
- PNG 13개 + GIF 3개, 72dpi, RGB
- 정사각 540x540 / 가로 540x300 / 세로 300x540, ≤1MB/개, 총 16개
"""

import io

from PIL import Image

from app.converters.base import decode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

DPI = (72, 72)
PADDING = 10  # 상하좌우 여백

# 사이즈 정의
KAKAO_SIZES = {
    "standard": (360, 360),  # 멈춰있는 / 움직이는
    "large_square": (540, 540),  # 큰이모티콘 정사각
    "large_wide": (540, 300),  # 큰이모티콘 가로
    "large_tall": (300, 540),  # 큰이모티콘 세로
}

# 용량 제한 (bytes)
SIZE_LIMITS = {
    "standard": 150 * 1024,  # 150KB (멈춰있는 이모티콘)
    "animated": 650 * 1024,  # 650KB (움직이는 이모티콘)
    "large_square": 1024 * 1024,  # 1MB
    "large_wide": 1024 * 1024,
    "large_tall": 1024 * 1024,
}

# 카카오 이모티콘 세트 개수 제한
KAKAO_COUNT_LIMITS = {
    "standard": 32,  # 멈춰있는 이모티콘: PNG 32개
    "animated": 24,  # 움직이는 이모티콘: PNG 21개 + GIF 3개
    "large": 16,  # 큰 이모티콘: PNG 13개 + GIF 3개
}


def _fit_to_canvas(
    img: Image.Image,
    canvas_size: tuple[int, int],
    padding: int = PADDING,
) -> Image.Image:
    """이미지를 캔버스에 여백 포함해서 중앙 배치."""
    # 여백을 뺀 영역에 맞추기
    inner_w = canvas_size[0] - padding * 2
    inner_h = canvas_size[1] - padding * 2
    img_copy = img.copy()
    img_copy.thumbnail((inner_w, inner_h), Image.LANCZOS)

    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    offset = (
        (canvas_size[0] - img_copy.width) // 2,
        (canvas_size[1] - img_copy.height) // 2,
    )
    canvas.paste(img_copy, offset, img_copy)
    return canvas


def _optimize_size(img: Image.Image, max_bytes: int) -> str:
    """용량 제한 내로 PNG 최적화. 초과 시 리사이즈.

    Raises:
        ValueError: 최소 스케일까지 축소해도 용량 초과 시
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=DPI, optimize=True)

    scale = 0.9
    max_attempts = 7
    for _ in range(max_attempts):
        if buf.tell() <= max_bytes:
            break
        new_size = (int(img.width * scale), int(img.height * scale))
        resized = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG", dpi=DPI, optimize=True)
        scale -= 0.1

    if buf.tell() > max_bytes:
        raise ValueError(
            f"이미지 최적화 실패: 최소 크기로 축소해도 용량 제한({max_bytes // 1024}KB)을 초과합니다"
        )

    import base64

    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def convert_kakao(
    emojis: list[EmojiResult],
    variant: str = "standard",
) -> list[ConvertedEmoji]:
    """Convert emoji set to Kakao emoticon format.

    Args:
        emojis: 이모지 리스트
        variant: "standard" (360x360), "large_square" (540x540),
                 "large_wide" (540x300), "large_tall" (300x540)

    Raises:
        ValueError: 카카오 규격 개수 초과 시
    """
    count_category = "large" if variant.startswith("large") else variant
    max_count = KAKAO_COUNT_LIMITS.get(count_category, KAKAO_COUNT_LIMITS["standard"])
    if len(emojis) > max_count:
        raise ValueError(
            f"카카오 {count_category} 이모티콘은 최대 {max_count}개입니다 (입력: {len(emojis)}개)"
        )

    canvas_size = KAKAO_SIZES.get(variant, KAKAO_SIZES["standard"])
    max_bytes = SIZE_LIMITS.get(variant, SIZE_LIMITS["standard"])

    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        canvas = _fit_to_canvas(img, canvas_size)
        image_url = _optimize_size(canvas, max_bytes)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=image_url,
                format=f"kakao_{variant}",
                width=canvas_size[0],
                height=canvas_size[1],
            )
        )

    return results
