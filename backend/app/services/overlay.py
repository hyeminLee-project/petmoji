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
_MAX_TEXT_RATIO = 0.9  # 텍스트 최대 폭 (이미지 폭 대비)
_LINE_SPACING = 1.15
_MAX_LINES = 2


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """한국어 폰트 로드. 폰트 파일이 없으면 기본 폰트 사용."""
    try:
        return ImageFont.truetype(str(_FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font, stroke_width: int) -> int:
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    return bbox[2] - bbox[0]


def _split_two_lines(caption: str) -> list[str]:
    """중앙에 가장 가까운 공백에서 두 줄로 분할. 공백이 없으면 글자 중간에서 분할."""
    spaces = [i for i, ch in enumerate(caption) if ch == " "]
    if spaces:
        split = min(spaces, key=lambda i: abs(i - len(caption) // 2))
        return [caption[:split], caption[split + 1 :]]
    mid = len(caption) // 2
    return [caption[:mid], caption[mid:]]


def _fit_caption_lines(
    draw: ImageDraw.ImageDraw, caption: str, width: int
) -> tuple[list[str], ImageFont.FreeTypeFont, int]:
    """캡션을 최대 2줄에 맞추고, 넘치면 폰트를 줄여가며 맞춘다.

    Returns:
        (줄 목록, 폰트, 스트로크 폭)
    """
    max_width = int(width * _MAX_TEXT_RATIO)
    font_size = max(22, width // 13)
    min_font_size = max(16, width // 20)

    while True:
        font = _load_font(font_size)
        stroke_width = max(3, font_size // 6)

        if _text_width(draw, caption, font, stroke_width) <= max_width:
            return [caption], font, stroke_width

        lines = _split_two_lines(caption)
        if all(_text_width(draw, line, font, stroke_width) <= max_width for line in lines):
            return lines, font, stroke_width

        if font_size <= min_font_size:
            return lines, font, stroke_width
        font_size = max(min_font_size, int(font_size * 0.9))


def render_caption_layer(size: tuple[int, int], caption: str) -> Image.Image | None:
    """캡션 텍스트만 그린 투명 레이어를 생성한다.

    최종 출력 해상도에서 직접 렌더링하므로 리샘플링 없이 선명하다.
    GIF처럼 여러 프레임에 같은 캡션을 합성할 때 재사용한다.
    긴 대사는 최대 2줄로 감싸고, 그래도 넘치면 폰트를 축소한다.

    Args:
        size: 레이어 크기 (최종 출력 해상도)
        caption: 렌더링할 텍스트

    Returns:
        투명 배경 위 텍스트 레이어. 캡션이 비어있으면 None.
    """
    if not caption:
        return None

    width, _ = size
    text_layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    lines, font, stroke_width = _fit_caption_lines(draw, caption, width)
    line_height = int(font.size * _LINE_SPACING)

    y = _MARGIN_TOP
    for line in lines[:_MAX_LINES]:
        text_w = _text_width(draw, line, font, stroke_width)
        draw.text(
            ((width - text_w) // 2, y),
            line,
            font=font,
            fill=_TEXT_COLOR,
            stroke_width=stroke_width,
            stroke_fill=_STROKE_COLOR,
        )
        y += line_height

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
