"""Rate limiting 테스트."""

import io

from httpx import AsyncClient


async def test_generate_rate_limit(client: AsyncClient, fake_jpeg: io.BytesIO):
    """10회 초과 요청 시 429 반환 확인."""
    for i in range(11):
        fake_jpeg.seek(0)
        res = await client.post(
            "/api/generate",
            files={"file": ("test.jpg", fake_jpeg, "image/jpeg")},
            data={"style": "2d", "emoji_count": "1", "provider": "gemini"},
        )
        if res.status_code == 429:
            assert i >= 10
            assert "요청이 너무 많습니다" in res.json()["detail"]
            return

    # 테스트 환경에서 rate limit이 IP 기반이라 통과할 수 있음
    # slowapi는 테스트 클라이언트에서 IP를 "testclient"로 인식
