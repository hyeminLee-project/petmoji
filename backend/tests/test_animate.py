"""움직이는 이모지 생성 API 테스트"""

import io
import tempfile

import imageio.v2 as imageio
import numpy as np
import pytest
from httpx import AsyncClient
from PIL import Image

from app.converters.video import video_to_pingpong_gif


def _make_test_mp4(num_frames: int = 48, size: int = 128) -> bytes:
    """움직이는 사각형이 담긴 짧은 테스트 mp4 생성."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        path = f.name
    writer = imageio.get_writer(path, format="ffmpeg", fps=24)
    for i in range(num_frames):
        frame = np.full((size, size, 3), 255, dtype=np.uint8)
        x = 20 + i * 2
        frame[40:80, x : x + 30] = [255, 150, 50]
        writer.append_data(frame)
    writer.close()
    with open(path, "rb") as f:
        return f.read()


# ─── video_to_pingpong_gif ─────────────────────────


def test_pingpong_gif_conversion():
    """mp4 → 핑퐁 루프 GIF 변환: 프레임 수와 크기 확인"""
    video = _make_test_mp4()
    gif_url = video_to_pingpong_gif(video, caption="")

    assert gif_url.startswith("data:image/gif;base64,")

    import base64

    raw = base64.b64decode(gif_url.split(",", 1)[1])
    gif = Image.open(io.BytesIO(raw))
    assert gif.size == (360, 360)
    # 48프레임/24fps 영상 → 10fps 1.6초 = 16프레임 추출 → 핑퐁 = 16 + 14 = 30
    assert gif.n_frames == 30


def test_pingpong_gif_loop_symmetry():
    """핑퐁 루프: 마지막 프레임 다음이 첫 프레임과 자연스럽게 이어짐 (2번째 == 뒤에서 1번째)"""
    video = _make_test_mp4()
    gif_url = video_to_pingpong_gif(video, caption="")

    import base64

    raw = base64.b64decode(gif_url.split(",", 1)[1])
    gif = Image.open(io.BytesIO(raw))
    gif.seek(1)
    second = list(gif.convert("RGB").getdata())
    gif.seek(gif.n_frames - 1)
    last = list(gif.convert("RGB").getdata())
    diff = sum(1 for a, b in zip(second, last, strict=True) if a != b)
    # GIF 팔레트 양자화 오차 허용 (전체 픽셀의 1% 미만)
    assert diff < len(second) * 0.01


def test_pingpong_gif_with_caption():
    """캡션 포함 변환: 상단에 불투명한 어두운 텍스트 픽셀 존재"""
    video = _make_test_mp4()
    gif_url = video_to_pingpong_gif(video, caption="좋아좋아!")

    import base64

    raw = base64.b64decode(gif_url.split(",", 1)[1])
    gif = Image.open(io.BytesIO(raw))
    top = gif.convert("RGBA").crop((0, 0, 360, 80))
    dark = sum(1 for r, g, b, a in top.getdata() if a > 128 and r < 100 and g < 100 and b < 100)
    assert dark > 50


def test_pingpong_gif_transparent_background():
    """흰 배경 영상 → 투명 배경 GIF (모서리 투명, 캐릭터 불투명)"""
    video = _make_test_mp4()
    gif_url = video_to_pingpong_gif(video, caption="")

    import base64

    raw = base64.b64decode(gif_url.split(",", 1)[1])
    gif = Image.open(io.BytesIO(raw))
    assert "transparency" in gif.info

    frame = gif.convert("RGBA")
    assert frame.getpixel((5, 5))[3] == 0  # 모서리는 투명
    # 캐릭터(주황 사각형, 원본 40~80행 → 360 스케일에서 y 112~225) 영역은 불투명
    center = frame.crop((80, 130, 280, 200))
    opaque = sum(1 for _, _, _, a in center.getdata() if a > 128)
    assert opaque > 1000


def test_flatten_transparency():
    """투명 PNG 입력을 흰 배경으로 평탄화"""
    import base64

    from app.services.animator import _flatten_transparency

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    for x in range(20, 44):
        for y in range(20, 44):
            img.putpixel((x, y), (255, 100, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    flat_url = _flatten_transparency(url)
    flat = Image.open(io.BytesIO(base64.b64decode(flat_url.split(",", 1)[1])))
    assert flat.convert("RGBA").getpixel((0, 0)) == (255, 255, 255, 255)
    assert flat.convert("RGBA").getpixel((32, 32))[:3] == (255, 100, 0)

    # 불투명 이미지는 그대로 반환
    opaque_img = Image.new("RGBA", (64, 64), (255, 255, 255, 255))
    buf2 = io.BytesIO()
    opaque_img.save(buf2, format="PNG")
    opaque_url = "data:image/png;base64," + base64.b64encode(buf2.getvalue()).decode()
    assert _flatten_transparency(opaque_url) == opaque_url


# ─── POST /api/animate ─────────────────────────


async def test_animate_free_tier_forbidden(client: AsyncClient, sample_image_b64: str):
    """무료 티어는 403"""
    res = await client.post(
        "/api/animate",
        json={
            "emoji": {"emotion": "happy", "image_url": sample_image_b64},
            "tier": "free",
        },
    )
    assert res.status_code == 403


async def test_animate_not_configured(
    client: AsyncClient, sample_image_b64: str, monkeypatch: pytest.MonkeyPatch
):
    """영상 프로바이더 미설정 시 503"""
    for env in ("RUNWAY_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "VIDEO_PROVIDER"):
        monkeypatch.delenv(env, raising=False)
    res = await client.post(
        "/api/animate",
        json={
            "emoji": {"emotion": "happy", "image_url": sample_image_b64},
            "tier": "premium",
        },
    )
    assert res.status_code == 503


async def test_animate_happy_path(
    client: AsyncClient, sample_image_b64: str, monkeypatch: pytest.MonkeyPatch
):
    """영상 생성을 mock하고 전체 플로우 확인"""
    monkeypatch.setenv("RUNWAY_API_KEY", "test-key")
    video = _make_test_mp4()

    async def fake_generate(image_data_url: str, emotion: str) -> bytes:
        return video

    import app.routers.animate as animate_module

    monkeypatch.setattr(animate_module, "generate_motion_video", fake_generate)

    res = await client.post(
        "/api/animate",
        json={
            "emoji": {"emotion": "happy", "image_url": sample_image_b64, "caption": "신난다!"},
            "tier": "premium",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "animated"
    assert data["width"] == 360
    assert data["image_url"].startswith("data:image/gif;base64,")
