"""비전 캡션(그림 보고 대사 생성) 테스트"""

import json

import pytest

import app.services.caption as caption_module
from app.models.schemas import PetFeatures
from app.services.caption import CAPTION_FALLBACKS, generate_caption_for_image

FEATURES = PetFeatures(
    animal_type="dog",
    breed="Poodle",
    fur_color="white",
    fur_pattern="solid",
    ear_shape="floppy",
    eye_color="black",
    eye_shape="round",
    nose_shape="small",
    body_shape="fluffy",
    distinctive_features=["curly fur"],
    current_expression="happy",
    overall_vibe="playful",
)

IMAGE_URL = "data:image/png;base64,aGVsbG8="


def _fake_vision(caption: str):
    async def fake(image_data_url: str, system: str) -> str:
        return json.dumps({"caption": caption}, ensure_ascii=False)

    return fake


async def test_valid_vision_caption_returned(monkeypatch: pytest.MonkeyPatch):
    """검증 통과한 비전 캡션은 그대로 사용"""
    monkeypatch.setattr(
        caption_module, "_vision_caption_with_gemini", _fake_vision("간식 줄 시간 아냐?")
    )
    caption = await generate_caption_for_image(IMAGE_URL, "hungry", FEATURES, "gemini")
    assert caption == "간식 줄 시간 아냐?"


async def test_invalid_vision_caption_falls_back(monkeypatch: pytest.MonkeyPatch):
    """검증 탈락(외국 문자 등) 시 fallback 사용"""
    monkeypatch.setattr(caption_module, "_vision_caption_with_gemini", _fake_vision("お腹すいた!"))
    caption = await generate_caption_for_image(IMAGE_URL, "hungry", FEATURES, "gemini")
    assert caption in CAPTION_FALLBACKS["hungry"]


async def test_vision_failure_falls_back(monkeypatch: pytest.MonkeyPatch):
    """비전 호출 실패 시 fallback 사용"""

    async def failing(image_data_url: str, system: str) -> str:
        raise RuntimeError("vision down")

    monkeypatch.setattr(caption_module, "_vision_caption_with_gemini", failing)
    caption = await generate_caption_for_image(IMAGE_URL, "happy", FEATURES, "gemini")
    assert caption in CAPTION_FALLBACKS["happy"]


async def test_accepts_dict_features(monkeypatch: pytest.MonkeyPatch):
    """위자드 상태의 dict 형태 pet_features도 수용"""
    monkeypatch.setattr(
        caption_module, "_vision_caption_with_gemini", _fake_vision("오늘 최고의 날!")
    )
    caption = await generate_caption_for_image(IMAGE_URL, "happy", FEATURES.model_dump(), "gemini")
    assert caption == "오늘 최고의 날!"


async def test_emotion_hint_in_system_prompt(monkeypatch: pytest.MonkeyPatch):
    """시스템 프롬프트에 감정 힌트와 성격이 포함됨"""
    seen: dict = {}

    async def capture(image_data_url: str, system: str) -> str:
        seen["system"] = system
        return json.dumps({"caption": "오늘 최고의 날!"})

    monkeypatch.setattr(caption_module, "_vision_caption_with_gemini", capture)
    await generate_caption_for_image(IMAGE_URL, "sleepy", FEATURES, "gemini")
    assert "sleepy" in seen["system"]
    assert "playful" in seen["system"]
