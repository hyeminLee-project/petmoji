"""위자드 API 테스트 (LangGraph mock)"""

import io
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.models.schemas import PetFeatures

MOCK_FEATURES = PetFeatures(
    animal_type="dog",
    breed="Labrador Retriever",
    fur_color="golden",
    fur_pattern="solid",
    ear_shape="floppy",
    eye_color="brown",
    eye_shape="round",
    nose_shape="round",
    body_shape="chubby",
    distinctive_features=["curly tail"],
    current_expression="happy",
    overall_vibe="cute",
)


MOCK_IMAGE_URL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg=="


async def test_wizard_start_free(client: AsyncClient, fake_jpeg: io.BytesIO):
    """무료 티어 위자드 시작 — 분석 결과 반환"""
    with (
        patch(
            "app.graph.nodes.analyze_pet_photo",
            new_callable=AsyncMock,
            return_value=MOCK_FEATURES,
        ),
        patch(
            "app.graph.nodes.PROVIDERS",
            {"gemini": AsyncMock(return_value=MOCK_IMAGE_URL)},
        ),
    ):
        res = await client.post(
            "/api/wizard/start",
            files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
            data={"tier": "free", "provider": "gemini", "analyzer": "gemini"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert "session_token" in data
    assert data["pet_features"]["breed"] == "Labrador Retriever"
    assert "tier_config" in data


async def test_wizard_start_premium(client: AsyncClient, fake_jpeg: io.BytesIO):
    """프리미엄 티어 위자드 시작"""
    with (
        patch(
            "app.graph.nodes.analyze_pet_photo",
            new_callable=AsyncMock,
            return_value=MOCK_FEATURES,
        ),
        patch(
            "app.graph.nodes.PROVIDERS",
            {"gemini": AsyncMock(return_value=MOCK_IMAGE_URL)},
        ),
    ):
        res = await client.post(
            "/api/wizard/start",
            files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
            data={"tier": "premium", "provider": "gemini", "analyzer": "gemini"},
        )

    assert res.status_code == 200
    data = res.json()
    assert data["tier_config"]["guided_wizard"] is True
    assert data["tier_config"]["max_emotions"] == 16


async def test_wizard_start_invalid_file(client: AsyncClient):
    """빈 파일로 위자드 시작 실패"""
    res = await client.post(
        "/api/wizard/start",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
        data={"tier": "free"},
    )
    assert res.status_code == 400


async def test_wizard_start_invalid_content_type(client: AsyncClient):
    """지원하지 않는 형식"""
    res = await client.post(
        "/api/wizard/start",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
        data={"tier": "free"},
    )
    assert res.status_code == 400


async def test_wizard_step_no_token(client: AsyncClient):
    """토큰 없이 step 호출 → 401"""
    res = await client.post(
        "/api/wizard/step",
        json={
            "session_id": "nonexistent",
            "step": "style",
            "selection": {"style": "2d"},
        },
    )
    assert res.status_code == 401


async def test_wizard_step_invalid_token(client: AsyncClient):
    """잘못된 토큰으로 step 호출 → 403"""
    res = await client.post(
        "/api/wizard/step",
        json={
            "session_id": "nonexistent",
            "step": "style",
            "selection": {"style": "2d"},
        },
        headers={"X-Session-Token": "invalid-token"},
    )
    assert res.status_code == 403


async def test_wizard_back_no_token(client: AsyncClient):
    """토큰 없이 back 호출 → 401"""
    res = await client.post(
        "/api/wizard/back",
        json={"session_id": "nonexistent", "target_step": "style"},
    )
    assert res.status_code == 401


async def test_wizard_generate_no_token(client: AsyncClient):
    """토큰 없이 generate 호출 → 401"""
    res = await client.post(
        "/api/wizard/generate",
        json={"session_id": "nonexistent", "emoji_count": 8},
    )
    assert res.status_code == 401
