"""생동감 캡션 생성/렌더링 테스트"""

from PIL import Image, ImageDraw

from app.services.caption import CAPTION_FALLBACKS, MAX_CAPTION_LENGTH
from app.services.overlay import _fit_caption_lines, render_caption_layer

CANVAS = (360, 360)


def test_fallbacks_fit_render_limit():
    """모든 fallback 캡션이 렌더 한계 길이 이내"""
    for emotion, options in CAPTION_FALLBACKS.items():
        for caption in options:
            assert len(caption) <= MAX_CAPTION_LENGTH, f"{emotion}: '{caption}' too long"


def test_fallbacks_are_not_fragmentary():
    """fallback이 단편적 감탄사가 아닌 대사 형태 (4자 이상)"""
    for emotion, options in CAPTION_FALLBACKS.items():
        for caption in options:
            assert len(caption) >= 4, f"{emotion}: '{caption}' too fragmentary"


def test_short_caption_single_line():
    """짧은 캡션은 한 줄 유지"""
    draw = ImageDraw.Draw(Image.new("RGBA", CANVAS))
    lines, _, _ = _fit_caption_lines(draw, "안녕!", 360)
    assert lines == ["안녕!"]


def test_long_caption_wraps_to_two_lines():
    """긴 캡션은 공백 기준 두 줄로 분할"""
    draw = ImageDraw.Draw(Image.new("RGBA", CANVAS))
    caption = "배에서 천둥소리가 계속 들려온다니까"
    lines, _, _ = _fit_caption_lines(draw, caption, 360)
    assert len(lines) == 2
    assert "".join(lines).replace(" ", "") == caption.replace(" ", "")


def test_long_caption_without_space_splits_mid():
    """공백 없는 긴 캡션은 중간에서 분할"""
    draw = ImageDraw.Draw(Image.new("RGBA", CANVAS))
    lines, _, _ = _fit_caption_lines(draw, "가나다라마바사아자차카타파하", 360)
    assert len(lines) == 2


def test_render_two_line_caption_visible():
    """두 줄 캡션이 실제로 두 줄 높이에 렌더링됨"""
    layer = render_caption_layer(CANVAS, "밥 주세요 제발 배고파요 진짜")
    assert layer is not None

    alpha = layer.getchannel("A")
    rows_with_text = [
        y for y in range(layer.height) if any(alpha.getpixel((x, y)) > 0 for x in range(0, 360, 4))
    ]
    # 한 줄 폰트 높이(~28px)보다 확실히 큰 세로 범위를 차지해야 두 줄
    assert rows_with_text[-1] - rows_with_text[0] > 40
