"""움직이는 이모지 GIF 변환기.

이모지 세트를 프레임 애니메이션 GIF로 변환.
각 이모지가 순서대로 표시되는 슬라이드쇼 + 개별 바운스 GIF.
"""

from PIL import Image

from app.converters.base import decode_image, encode_gif, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

GIF_SIZE = (256, 256)
FRAME_DURATION = 400  # ms per frame


def _create_bounce_frames(img: Image.Image, num_frames: int = 6) -> list[Image.Image]:
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

        canvas = Image.new("RGBA", GIF_SIZE, (255, 255, 255, 255))
        offset = (
            (GIF_SIZE[0] - img.width) // 2,
            (GIF_SIZE[1] - img.height) // 2 + y_offset,
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

        results.append(ConvertedEmoji(
            emotion=emoji.emotion,
            image_url=gif_url,
            format="gif",
            width=GIF_SIZE[0],
            height=GIF_SIZE[1],
        ))

    return results
