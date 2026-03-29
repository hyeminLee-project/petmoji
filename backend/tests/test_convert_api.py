"""변환 API 엔드포인트 테스트"""

from httpx import AsyncClient

from app.models.schemas import EmojiResult


async def test_formats_list(client: AsyncClient):
    """GET /api/formats — 5개 포맷 목록"""
    res = await client.get("/api/formats")
    assert res.status_code == 200
    data = res.json()
    assert len(data["formats"]) == 5
    ids = {f["id"] for f in data["formats"]}
    assert ids == {"kakao", "imessage", "sticker", "gif", "wallpaper"}


async def test_formats_have_required_fields(client: AsyncClient):
    """각 포맷에 id, name, size 필드 존재"""
    res = await client.get("/api/formats")
    for fmt in res.json()["formats"]:
        assert "id" in fmt
        assert "name" in fmt
        assert "size" in fmt


async def test_convert_kakao(client: AsyncClient, sample_emojis: list[EmojiResult]):
    """POST /api/convert — kakao 변환 성공"""
    res = await client.post(
        "/api/convert",
        json={
            "emojis": [e.model_dump() for e in sample_emojis],
            "format": "kakao",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "kakao"
    assert len(data["emojis"]) == 2


async def test_convert_invalid_format(client: AsyncClient, sample_emojis: list[EmojiResult]):
    """잘못된 포맷"""
    res = await client.post(
        "/api/convert",
        json={
            "emojis": [e.model_dump() for e in sample_emojis],
            "format": "invalid",
        },
    )
    assert res.status_code == 400


async def test_convert_empty_emojis(client: AsyncClient):
    """빈 이모지 리스트"""
    res = await client.post(
        "/api/convert",
        json={
            "emojis": [],
            "format": "kakao",
        },
    )
    assert res.status_code == 400
