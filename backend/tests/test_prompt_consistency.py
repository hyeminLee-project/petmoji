"""프롬프트 빌딩·포맷 레지스트리 일관성 테스트"""

from app.converters import FORMAT_REGISTRY
from app.graph import prompts
from app.services import generator
from app.services.generator import (
    BACKGROUND_DESCRIPTIONS,
    EMOTIONS,
    PLAIN_BACKGROUNDS,
    build_prompt_suffix,
)


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


def test_plain_backgrounds_are_registered():
    """PLAIN_BACKGROUNDS는 BACKGROUND_DESCRIPTIONS의 부분집합"""
    for bg in PLAIN_BACKGROUNDS:
        assert bg in BACKGROUND_DESCRIPTIONS


def test_emotions_count_matches_frontend():
    """감정 32종 — 프론트 EMOTION_LABELS와 동기화 (EmojiGrid.tsx)"""
    assert len(EMOTIONS) == 32
    assert len({e for e, _ in EMOTIONS}) == 32  # 중복 키 없음


def test_format_registry_complete():
    """레지스트리 모든 포맷에 필수 메타데이터 존재"""
    required = {"converter", "name", "icon", "size", "limit", "max_count", "description"}
    for format_id, meta in FORMAT_REGISTRY.items():
        assert required <= set(meta), f"{format_id}: 누락 키 {required - set(meta)}"
        assert callable(meta["converter"])
        assert meta["max_count"] > 0
