"""이모지 이미지 위에 말풍선 캡션을 오버레이하는 유틸리티.

Pillow를 사용하여 이미지 하단에 반투명 말풍선 + 한국어 텍스트를 합성한다.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "NotoSansKR-Bold.ttf"

# 말풍선 스타일
_BUBBLE_COLOR = (255, 255, 255, 210)  # 반투명 흰색
_BUBBLE_OUTLINE_COLOR = (180, 180, 180, 255)  # 연한 회색 테두리
_TEXT_COLOR = (50, 50, 50, 255)  # 진한 회색 텍스트
_BUBBLE_PADDING_X = 16
_BUBBLE_PADDING_Y = 8
_BUBBLE_RADIUS = 14
_BUBBLE_MARGIN_BOTTOM = 12  # 이미지 하단으로부터의 여백


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한국어 폰트 로드. 폰트 파일이 없으면 기본 폰트 사용."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def overlay_caption(image: Image.Image, caption: str) -> Image.Image:
    """이미지 하단에 말풍선 캡션을 오버레이한다.

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

    # 이미지 크기에 비례하는 폰트 크기 (1024px → ~56px, 360px → ~20px)
    font_size = max(16, img.width // 18)
    font = _load_font(font_size)

    # 텍스트 크기 측정
    temp_draw = ImageDraw.Draw(img)
    text_bbox = temp_draw.textbbox((0, 0), caption, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # 말풍선 크기
    bubble_w = text_w + _BUBBLE_PADDING_X * 2
    bubble_h = text_h + _BUBBLE_PADDING_Y * 2

    # 말풍선 위치 (하단 중앙)
    bubble_x = (img.width - bubble_w) // 2
    bubble_y = img.height - bubble_h - _BUBBLE_MARGIN_BOTTOM

    # 말풍선 레이어 (반투명 처리를 위해 별도 레이어)
    bubble_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bubble_layer)

    # 둥근 사각형 말풍선
    draw.rounded_rectangle(
        [bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h],
        radius=_BUBBLE_RADIUS,
        fill=_BUBBLE_COLOR,
        outline=_BUBBLE_OUTLINE_COLOR,
        width=2,
    )

    # 텍스트 (말풍선 중앙)
    text_x = bubble_x + _BUBBLE_PADDING_X
    text_y = bubble_y + _BUBBLE_PADDING_Y
    draw.text((text_x, text_y), caption, font=font, fill=_TEXT_COLOR)

    # 합성
    return Image.alpha_composite(img, bubble_layer)
