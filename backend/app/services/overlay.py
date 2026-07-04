"""이모지 이미지 위에 이모티콘 스타일 캡션을 오버레이하는 유틸리티.

카카오/라인 이모티콘처럼 그림 안에 굵은 텍스트 + 흰색 테두리(스트로크)를
직접 배치한다. 말풍선 없이 텍스트가 그림과 어우러지는 스타일.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONT_PATH = Path(__file__).parent.parent / "assets" / "fonts" / "NotoSansKR-Bold.ttf"

# 텍스트 스타일
_TEXT_COLOR = (30, 30, 30, 255)  # 거의 검정 본문
_STROKE_COLOR = (255, 255, 255, 255)  # 흰색 테두리
_MARGIN_TOP = 20  # 이미지 상단으로부터의 여백


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한국어 폰트 로드. 폰트 파일이 없으면 기본 폰트 사용."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def render_caption_layer(size: tuple[int, int], caption: str) -> Image.Image | None:
    """캡션 텍스트만 그린 투명 레이어를 생성한다.

    최종 출력 해상도에서 직접 렌더링하므로 리샘플링 없이 선명하다.
    GIF처럼 여러 프레임에 같은 캡션을 합성할 때 재사용한다.

    Args:
        size: 레이어 크기 (최종 출력 해상도)
        caption: 렌더링할 텍스트

    Returns:
        투명 배경 위 텍스트 레이어. 캡션이 비어있으면 None.
    """
    if not caption:
        return None

    width, _ = size
    # 이미지 크기에 비례하는 폰트 크기 (360px → ~28px, 256px → ~22px)
    font_size = max(22, width // 13)
    font = _load_font(font_size)
    stroke_width = max(3, font_size // 6)

    text_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    # 텍스트 크기 측정 (스트로크 포함) → 상단 중앙 배치
    text_bbox = draw.textbbox((0, 0), caption, font=font, stroke_width=stroke_width)
    text_w = text_bbox[2] - text_bbox[0]
    text_x = (width - text_w) // 2
    text_y = _MARGIN_TOP

    draw.text(
        (text_x, text_y),
        caption,
        font=font,
        fill=_TEXT_COLOR,
        stroke_width=stroke_width,
        stroke_fill=_STROKE_COLOR,
    )

    return text_layer


def overlay_caption(image: Image.Image, caption: str) -> Image.Image:
    """이미지 위에 이모티콘 스타일 텍스트를 오버레이한다.

    말풍선 없이 굵은 텍스트 + 흰색 스트로크로 그림 안에 직접 배치.

    Args:
        image: 원본 이미지 (RGBA)
        caption: 오버레이할 텍스트

    Returns:
        캡션이 합성된 새 이미지
    """
    text_layer = render_caption_layer(image.size, caption)
    if text_layer is None:
        return image

    img = image.copy()
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    return Image.alpha_composite(img, text_layer)
