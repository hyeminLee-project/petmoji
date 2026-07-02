"""영상 → 움직이는 이모티콘 GIF 변환기.

Runway 등 비디오 모델의 mp4 출력을 카카오 규격 GIF로 변환한다.
- 앞부분 일부 구간만 사용 (모션이 가장 또렷한 초반)
- 핑퐁 루프(정방향 → 역방향)로 시작/끝 프레임 불연속 해결
- 캡션은 전 프레임 고정 합성 (gif.py와 동일한 원칙)
"""

import os
import tempfile

import imageio.v2 as imageio
from PIL import Image

from app.converters.gif import _optimize_gif_size
from app.converters.kakao import SIZE_LIMITS as KAKAO_SIZE_LIMITS
from app.services.overlay import render_caption_layer

VIDEO_GIF_SIZE = (360, 360)
TARGET_SECONDS = 1.6  # 사용할 영상 구간
TARGET_FPS = 10
FRAME_DURATION_MS = 100


def _extract_frames(video_bytes: bytes) -> list[Image.Image]:
    """mp4에서 앞부분 프레임을 목표 fps로 추출."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(video_bytes)
        path = f.name

    try:
        reader = imageio.get_reader(path, format="ffmpeg")
        meta = reader.get_meta_data()
        src_fps = meta.get("fps", 24)
        step = max(1, round(src_fps / TARGET_FPS))
        max_frames = int(TARGET_SECONDS * TARGET_FPS)

        frames: list[Image.Image] = []
        for i, frame in enumerate(reader):
            if i % step != 0:
                continue
            frames.append(Image.fromarray(frame).convert("RGBA"))
            if len(frames) >= max_frames:
                break
        reader.close()
    finally:
        os.unlink(path)

    if not frames:
        raise ValueError("영상에서 프레임을 추출할 수 없습니다")
    return frames


def _fit_square(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """중앙 정사각 크롭 후 목표 크기로 리사이즈."""
    side = min(img.size)
    left = (img.width - side) // 2
    top = (img.height - side) // 2
    return img.crop((left, top, left + side, top + side)).resize(size, Image.LANCZOS)


def video_to_pingpong_gif(
    video_bytes: bytes,
    caption: str = "",
    size: tuple[int, int] = VIDEO_GIF_SIZE,
    max_bytes: int = KAKAO_SIZE_LIMITS["animated"],
) -> str:
    """mp4 영상을 핑퐁 루프 GIF data URL로 변환."""
    frames = _extract_frames(video_bytes)
    frames = [_fit_square(f, size) for f in frames]

    caption_layer = render_caption_layer(size, caption)
    if caption_layer is not None:
        frames = [Image.alpha_composite(f, caption_layer) for f in frames]

    # 핑퐁: 정방향 + 역방향(양 끝 중복 제거) → 루프 불연속 제거
    pingpong = frames + frames[-2:0:-1]
    rgb_frames = [f.convert("RGB") for f in pingpong]

    return _optimize_gif_size(rgb_frames, max_bytes, FRAME_DURATION_MS)
