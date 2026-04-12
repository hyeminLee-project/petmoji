"""움직이는 이모지 GIF 변환기.

이모지 세트를 프레임 애니메이션 GIF로 변환.
각 이모지가 순서대로 표시되는 슬라이드쇼 + 개별 바운스 GIF.

카카오 움직이는 이모티콘 규격:
- 360x360px, 72dpi, ≤650KB/개, 총 24개 (PNG 21 + GIF 3)
"""

from PIL import Image

from app.converters.base import decode_image, encode_gif
from app.converters.kakao import KAKAO_COUNT_LIMITS
from app.converters.kakao import SIZE_LIMITS as KAKAO_SIZE_LIMITS
from app.models.schemas import ConvertedEmoji, EmojiResult

GIF_SIZE = (256, 256)
KAKAO_GIF_SIZE = (360, 360)
FRAME_DURATION = 400  # ms per frame


def _create_bounce_frames(
    img: Image.Image,
    num_frames: int = 6,
    size: tuple[int, int] = GIF_SIZE,
) -> list[Image.Image]:
    """Create a simple bounce animation from a single image."""
    frames: list[Image.Image] = []
    max_offset = 10  # pixels

    for i in range(num_frames):
        # Simple sine-wave-like bounce: 0, up, 0, down, 0, up
        if i % 3 == 0:
            y_offset = 0
        elif i % 3 == 1:
            y_offset = -max_offset
        else:
            y_offset = max_offset // 2

        canvas = Image.new("RGBA", size, (255, 255, 255, 255))
        offset = (
            (size[0] - img.width) // 2,
            (size[1] - img.height) // 2 + y_offset,
        )
        canvas.paste(img, offset, img)
        # Convert to RGB for GIF compatibility
        frames.append(canvas.convert("RGB"))

    return frames


def convert_gif(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """Convert each emoji to a bouncing animated GIF."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(GIF_SIZE, Image.LANCZOS)

        frames = _create_bounce_frames(img)
        gif_url = encode_gif(frames, duration=FRAME_DURATION)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=gif_url,
                format="gif",
                width=GIF_SIZE[0],
                height=GIF_SIZE[1],
            )
        )

    return results


def _optimize_gif_size(frames: list[Image.Image], max_bytes: int, duration: int) -> str:
    """GIF 용량 제한 내로 최적화. 초과 시 프레임 크기 축소.

    Raises:
        ValueError: 최소 스케일까지 축소해도 용량 초과 시
    """
    import base64

    gif_url = encode_gif(frames, duration=duration)
    b64_data = gif_url.split(",", 1)[1]
    raw = base64.b64decode(b64_data)

    if len(raw) <= max_bytes:
        return gif_url

    scale = 0.9
    max_attempts = 7
    for _ in range(max_attempts):
        new_size = (int(frames[0].width * scale), int(frames[0].height * scale))
        resized_frames = [f.resize(new_size, Image.LANCZOS) for f in frames]
        gif_url = encode_gif(resized_frames, duration=duration)
        b64_data = gif_url.split(",", 1)[1]
        raw = base64.b64decode(b64_data)
        if len(raw) <= max_bytes:
            return gif_url
        scale -= 0.1

    raise ValueError(
        f"GIF 최적화 실패: 최소 크기로 축소해도 용량 제한({max_bytes // 1024}KB)을 초과합니다"
    )


def convert_kakao_animated(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """카카오 움직이는 이모티콘 규격으로 GIF 변환 (360x360, ≤650KB)."""
    max_count = KAKAO_COUNT_LIMITS["animated"]
    if len(emojis) > max_count:
        raise ValueError(
            f"카카오 움직이는 이모티콘은 최대 {max_count}개입니다 (입력: {len(emojis)}개)"
        )

    max_bytes = KAKAO_SIZE_LIMITS["animated"]
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(KAKAO_GIF_SIZE, Image.LANCZOS)

        frames = _create_bounce_frames(img, size=KAKAO_GIF_SIZE)
        gif_url = _optimize_gif_size(frames, max_bytes, FRAME_DURATION)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=gif_url,
                format="kakao_animated",
                width=KAKAO_GIF_SIZE[0],
                height=KAKAO_GIF_SIZE[1],
            )
        )

    return results
