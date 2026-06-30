"""이모지 이미지 위에 이모티콘 스타일 캡션을 오버레이하는 유틸리티.

카카오/라인 이모티콘처럼 그림 안에 굵은 텍스트 + 흰색 테두리(스트로크)를
직접 배치한다. 말풍선 없이 텍스트가 그림과 어우러지는 스타일.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "NotoSansKR-Bold.ttf"

# 텍스트 스타일
_TEXT_COLOR = (50, 50, 50, 255)  # 진한 회색 본문
_STROKE_COLOR = (255, 255, 255, 255)  # 흰색 테두리
_MARGIN_BOTTOM = 16  # 이미지 하단으로부터의 여백


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한국어 폰트 로드. 폰트 파일이 없으면 기본 폰트 사용."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def overlay_caption(image: Image.Image, caption: str) -> Image.Image:
    """이미지 위에 이모티콘 스타일 텍스트를 오버레이한다.

    말풍선 없이 굵은 텍스트 + 흰색 스트로크로 그림 안에 직접 배치.

    Args:
        image: 원본 이미지 (RGBA)
        caption: 오버레이할 텍스트

    Returns:
        캡션이 합성된 새 이미지
    """
    if not caption:
        return image

    img = image.copy()
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # 이미지 크기에 비례하는 폰트 크기 (1024px → ~64px, 360px → ~22px)
    font_size = max(18, img.width // 16)
    font = _load_font(font_size)
    stroke_width = max(2, font_size // 8)

    # 텍스트 크기 측정 (스트로크 포함)
    temp_draw = ImageDraw.Draw(img)
    text_bbox = temp_draw.textbbox((0, 0), caption, font=font, stroke_width=stroke_width)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # 텍스트 위치: 하단 중앙
    text_x = (img.width - text_w) // 2
    text_y = img.height - text_h - _MARGIN_BOTTOM

    # 텍스트 레이어 (반투명 처리를 위해 별도 레이어)
    text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # 흰색 스트로크 + 본문 텍스트
    draw.text(
        (text_x, text_y),
        caption,
        font=font,
        fill=_TEXT_COLOR,
        stroke_width=stroke_width,
        stroke_fill=_STROKE_COLOR,
    )

    return Image.alpha_composite(img, text_layer)
