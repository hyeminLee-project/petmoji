"""PetMoji API 기본 테스트"""
import io

from httpx import AsyncClient


async def test_health(client: AsyncClient):
    """헬스체크 엔드포인트"""
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


async def test_generate_no_file(client: AsyncClient):
    """파일 없이 요청 시 422"""
    res = await client.post("/api/generate")
    assert res.status_code == 422


async def test_generate_invalid_style(client: AsyncClient):
    """잘못된 스타일 값"""
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_image, "image/jpeg")},
        data={"style": "invalid", "emoji_count": "8"},
    )
    assert res.status_code == 400


async def test_generate_invalid_count(client: AsyncClient):
    """잘못된 이모지 개수"""
    fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_image, "image/jpeg")},
        data={"style": "2d", "emoji_count": "100"},
    )
    assert res.status_code == 400
