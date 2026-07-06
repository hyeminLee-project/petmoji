"""캡션 규칙 검증기 · 구조화 출력 파싱 테스트"""

import json

from app.services.caption import (
    CAPTION_FALLBACKS,
    _parse_caption_items,
    validate_caption,
)

# ─── validate_caption ─────────────────────────


def test_all_fallbacks_pass_validation():
    """사람이 검수한 fallback 사전은 전부 검증 통과 (정본 보호)"""
    for emotion, options in CAPTION_FALLBACKS.items():
        for caption in options:
            assert validate_caption(caption), f"{emotion}: {caption!r} rejected"


def test_rejects_foreign_scripts():
    """한자·가나 혼입 차단"""
    assert not validate_caption("大好きだよ~!")
    assert not validate_caption("좋아 かわいい")
    assert not validate_caption("최고야 最高!")


def test_rejects_emoji_characters():
    """이모지 문자 혼입 차단 (렌더 폰트에 없음)"""
    assert not validate_caption("좋아요😀 최고")
    assert not validate_caption("사랑해🐶")


def test_rejects_decomposed_jamo():
    """조합되지 않은 자모(깨진 한글) 차단, 관용 낱자(ㅋㅠ)는 허용"""
    assert not validate_caption("ㅇㅏㄴㄴㅕㅇ하세요")
    assert not validate_caption("좋아ㅛ 최고")
    assert validate_caption("아 배 아파 ㅋㅋㅋ")
    assert validate_caption("눈물이 나 ㅠㅠ")


def test_rejects_length_violations():
    """4자 미만, 14자 초과 차단"""
    assert not validate_caption("좋아!")
    assert not validate_caption("이 대사는 열네 글자를 확실히 넘어간다")
    assert validate_caption("기분 째진다~!")


def test_rejects_no_substantial_hangul():
    """한글 음절 2자 미만(낱자·영문·기호만) 차단"""
    assert not validate_caption("ㅋㅋㅋㅋㅋ")
    assert not validate_caption("zzZ~!!")
    assert not validate_caption("!?~....")
    assert validate_caption("쿨쿨 zzZ~")


# ─── _parse_caption_items ─────────────────────────


def test_parse_gemini_array_form():
    """Gemini 구조화 출력(배열) 파싱"""
    raw = json.dumps(
        [
            {"emotion": "happy", "caption": "오늘 최고의 날!"},
            {"emotion": "sad", "caption": "나 좀 안아줘..."},
        ]
    )
    assert _parse_caption_items(raw) == {
        "happy": "오늘 최고의 날!",
        "sad": "나 좀 안아줘...",
    }


def test_parse_openai_wrapped_form():
    """OpenAI strict 모드 출력({captions: [...]}) 파싱"""
    raw = json.dumps({"captions": [{"emotion": "cool", "caption": "이 구역 짱은 나야"}]})
    assert _parse_caption_items(raw) == {"cool": "이 구역 짱은 나야"}


def test_parse_skips_items_without_emotion():
    """emotion 키가 비어 있는 항목은 무시"""
    raw = json.dumps([{"emotion": "", "caption": "x"}, {"emotion": "happy", "caption": "좋아"}])
    assert _parse_caption_items(raw) == {"happy": "좋아"}
