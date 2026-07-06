"""변환 API 엔드포인트 테스트"""

from httpx import AsyncClient

from app.models.schemas import EmojiResult


async def test_formats_list(client: AsyncClient):
    """GET /api/formats — FORMAT_REGISTRY의 전체 포맷 목록"""
    from app.converters import FORMAT_REGISTRY

    res = await client.get("/api/formats")
    assert res.status_code == 200
    data = res.json()
    ids = {f["id"] for f in data["formats"]}
    assert ids == set(FORMAT_REGISTRY.keys())
    assert "kakao" in ids
    assert "kakao_animated" in ids
    assert "kakao_submission" in ids


async def test_formats_have_required_fields(client: AsyncClient):
    """각 포맷에 프론트가 쓰는 필드 존재"""
    res = await client.get("/api/formats")
    for fmt in res.json()["formats"]:
        for field in ("id", "name", "icon", "size", "description", "max_count"):
            assert field in fmt, f"{fmt.get('id')}: {field} 누락"


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
