"""배경 제거 스티커 변환기.

흰색/단색 배경을 투명으로 변환하여 스티커용 PNG 생성.
외곽에 흰색 테두리를 추가하여 스티커 느낌 강화.
"""

import numpy as np
from PIL import Image, ImageFilter

from app.converters.base import decode_image, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult
from app.services.overlay import overlay_caption

STICKER_SIZE = (512, 512)
BORDER_WIDTH = 8


def _remove_white_background(img: Image.Image, threshold: int = 240) -> Image.Image:
    """Remove white-ish background pixels by making them transparent."""
    arr = np.array(img.convert("RGBA"))
    white = (arr[..., :3] > threshold).all(axis=2)
    arr[white, 3] = 0
    return Image.fromarray(arr)


def _add_sticker_border(img: Image.Image, border_width: int = BORDER_WIDTH) -> Image.Image:
    """Add a white outline border around non-transparent pixels."""
    alpha = img.split()[3]
    expanded = alpha.filter(ImageFilter.MaxFilter(border_width * 2 + 1))

    # 확장 마스크에는 있지만 원본은 투명한 픽셀 = 테두리 영역
    alpha_arr = np.array(alpha)
    border_mask = (np.array(expanded) > 0) & (alpha_arr == 0)

    border_arr = np.zeros((*alpha_arr.shape, 4), dtype=np.uint8)
    border_arr[border_mask] = (255, 255, 255, 255)

    # Composite: border behind original
    return Image.alpha_composite(Image.fromarray(border_arr), img)


def convert_sticker(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """Convert emoji set to transparent sticker PNGs with border."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)

        # Remove background
        img = _remove_white_background(img)

        # Resize
        img.thumbnail(STICKER_SIZE, Image.LANCZOS)
        canvas = Image.new("RGBA", STICKER_SIZE, (0, 0, 0, 0))
        offset = (
            (STICKER_SIZE[0] - img.width) // 2,
            (STICKER_SIZE[1] - img.height) // 2,
        )
        canvas.paste(img, offset, img)

        # Add sticker border
        canvas = _add_sticker_border(canvas)
        canvas = overlay_caption(canvas, emoji.caption)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=encode_image(canvas),
                format="sticker",
                width=STICKER_SIZE[0],
                height=STICKER_SIZE[1],
            )
        )

    return results
