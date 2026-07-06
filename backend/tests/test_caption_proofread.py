"""캡션 LLM 셀프 교정 테스트"""

import json

import pytest

import app.services.caption as caption_module
from app.services.caption import _proofread_captions


def _fake_llm(response_items: list[dict]):
    """구조화 출력 형태의 응답을 돌려주는 가짜 LLM 함수."""

    async def fake(system: str, user: str, temperature: float = 0.8) -> str:
        return json.dumps(response_items, ensure_ascii=False)

    return fake


async def test_proofread_applies_corrections(monkeypatch: pytest.MonkeyPatch):
    """맞춤법 교정 결과가 반영됨"""
    monkeypatch.setattr(
        caption_module,
        "_generate_with_gemini",
        _fake_llm([{"emotion": "happy", "caption": "오늘 최고가 됐어!"}]),
    )
    result = await _proofread_captions({"happy": "오늘 최고가 됬어!"}, "gemini")
    assert result == {"happy": "오늘 최고가 됐어!"}


async def test_proofread_reject_becomes_empty(monkeypatch: pytest.MonkeyPatch):
    """감정 불일치 REJECT는 빈 문자열 → 상위에서 fallback 대체"""
    monkeypatch.setattr(
        caption_module,
        "_generate_with_gemini",
        _fake_llm(
            [
                {"emotion": "happy", "caption": "REJECT"},
                {"emotion": "sad", "caption": "나 좀 안아줘..."},
            ]
        ),
    )
    result = await _proofread_captions(
        {"happy": "너무 슬프고 우울해", "sad": "나 좀 안아줘..."}, "gemini"
    )
    assert result["happy"] == ""
    assert result["sad"] == "나 좀 안아줘..."


async def test_proofread_failure_keeps_originals(monkeypatch: pytest.MonkeyPatch):
    """교정 호출 실패 시 원본 그대로 반환 (부가 단계)"""

    async def failing(system: str, user: str, temperature: float = 0.8) -> str:
        raise RuntimeError("api down")

    monkeypatch.setattr(caption_module, "_generate_with_gemini", failing)
    originals = {"happy": "오늘 최고의 날!"}
    assert await _proofread_captions(originals, "gemini") == originals


async def test_proofread_missing_emotion_keeps_original(monkeypatch: pytest.MonkeyPatch):
    """교정 응답에 누락된 감정은 원본 유지"""
    monkeypatch.setattr(
        caption_module,
        "_generate_with_gemini",
        _fake_llm([{"emotion": "happy", "caption": "오늘 최고!"}]),
    )
    result = await _proofread_captions({"happy": "오늘 최고!", "sad": "슬픈 날이야.."}, "gemini")
    assert result["sad"] == "슬픈 날이야.."


async def test_proofread_skips_hermes_and_empty():
    """hermes와 빈 입력은 교정 없이 통과"""
    originals = {"happy": "좋아!"}
    assert await _proofread_captions(originals, "hermes") == originals
    assert await _proofread_captions({}, "gemini") == {}
