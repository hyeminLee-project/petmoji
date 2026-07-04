"""프롬프트 빌딩 일관성 테스트"""

from app.graph import prompts
from app.services import generator
from app.services.generator import build_prompt_suffix


def test_suffix_clean_background_for_plain_backgrounds():
    """흰색/투명/그라디언트 배경은 clean background 지시 포함"""
    for bg in ("white", "transparent", "gradient"):
        assert "Clean background" in build_prompt_suffix(bg)


def test_suffix_omits_clean_background_for_scenes():
    """장면 배경(공원 등)은 clean background 지시를 생략"""
    for bg in ("park", "cafe", "beach", "night"):
        suffix = build_prompt_suffix(bg)
        assert "clean background" not in suffix.lower()
        assert "No text, no watermark." in suffix


def test_style_descriptions_single_source():
    """무료 플로우와 위자드가 같은 스타일 설명을 사용"""
    assert prompts.STYLE_DESCRIPTIONS is generator.STYLE_DESCRIPTIONS
