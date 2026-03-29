"""공유 테스트 fixtures"""

import base64
import io

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.main import app
from app.models.schemas import EmojiResult


@pytest.fixture
async def client():
    """FastAPI 테스트 클라이언트"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sample_image_b64() -> str:
    """100x100 빨간 RGBA PNG의 base64 data URL"""
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


@pytest.fixture
def sample_emojis(sample_image_b64: str) -> list[EmojiResult]:
    """테스트용 이모지 2개"""
    return [
        EmojiResult(emotion="happy", image_url=sample_image_b64),
        EmojiResult(emotion="sad", image_url=sample_image_b64),
    ]


@pytest.fixture
def fake_jpeg() -> io.BytesIO:
    """테스트용 JPEG 이미지"""
    img = Image.new("RGB", (50, 50), (255, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf
