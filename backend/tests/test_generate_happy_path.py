"""생성 API happy path 테스트 (AI API mock)"""

import io
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.models.schemas import EmojiResult, PetFeatures

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


async def test_generate_success(client: AsyncClient, sample_image_b64: str, fake_jpeg: io.BytesIO):
    """정상적인 이모지 생성 흐름 (mock)"""
    mock_emojis = [
        EmojiResult(emotion="happy", image_url=sample_image_b64),
    ]

    with (
        patch(
            "app.routers.emoji.analyze_pet_photo",
            new_callable=AsyncMock,
            return_value=MOCK_FEATURES,
        ),
        patch(
            "app.routers.emoji.generate_emoji_set", new_callable=AsyncMock, return_value=mock_emojis
        ),
    ):
        res = await client.post(
            "/api/generate",
            files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
            data={"style": "2d", "emoji_count": "1", "provider": "gemini", "analyzer": "gemini"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "pet_features" in data
    assert "emojis" in data
    assert data["pet_features"]["breed"] == "Labrador Retriever"
    assert len(data["emojis"]) == 1
    assert data["emojis"][0]["emotion"] == "happy"
