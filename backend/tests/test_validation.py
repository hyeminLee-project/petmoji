"""입력 검증 테스트"""

import io

from httpx import AsyncClient


async def test_invalid_provider(client: AsyncClient, fake_jpeg: io.BytesIO):
    """잘못된 provider"""
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
        data={"style": "2d", "provider": "invalid"},
    )
    assert res.status_code == 400


async def test_invalid_analyzer(client: AsyncClient, fake_jpeg: io.BytesIO):
    """잘못된 analyzer"""
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
        data={"style": "2d", "analyzer": "invalid"},
    )
    assert res.status_code == 400


async def test_prompt_too_long(client: AsyncClient, fake_jpeg: io.BytesIO):
    """프롬프트 500자 초과"""
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
        data={"style": "2d", "custom_prompt": "x" * 501},
    )
    assert res.status_code == 400


async def test_prompt_at_limit(client: AsyncClient, fake_jpeg: io.BytesIO):
    """프롬프트 정확히 500자 — 검증 통과 (AI 호출에서 실패하지만 400은 아님)"""
    res = await client.post(
        "/api/generate",
        files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
        data={"style": "2d", "custom_prompt": "x" * 500},
    )
    assert res.status_code != 400


async def test_unsupported_content_type(client: AsyncClient):
    """지원하지 않는 이미지 형식"""
    fake = io.BytesIO(b"not an image")
    res = await client.post(
        "/api/generate",
        files={"file": ("test.bmp", fake, "image/bmp")},
        data={"style": "2d"},
    )
    assert res.status_code == 400


async def test_file_too_large(client: AsyncClient):
    """10MB 초과 파일"""
    large = io.BytesIO(b"\x00" * (10 * 1024 * 1024 + 1))
    res = await client.post(
        "/api/generate",
        files={"file": ("big.jpg", large, "image/jpeg")},
        data={"style": "2d"},
    )
    assert res.status_code == 400


async def test_empty_file(client: AsyncClient):
    """빈 파일"""
    res = await client.post(
        "/api/generate",
        files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
        data={"style": "2d"},
    )
    assert res.status_code == 400
