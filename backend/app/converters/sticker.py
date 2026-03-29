"""배경 제거 스티커 변환기.

흰색/단색 배경을 투명으로 변환하여 스티커용 PNG 생성.
외곽에 흰색 테두리를 추가하여 스티커 느낌 강화.
"""

from PIL import Image, ImageFilter

from app.converters.base import decode_image, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

STICKER_SIZE = (512, 512)
BORDER_WIDTH = 8


def _remove_white_background(img: Image.Image, threshold: int = 240) -> Image.Image:
    """Remove white-ish background pixels by making them transparent."""
    img = img.convert("RGBA")
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (r, g, b, 0)

    return img


def _add_sticker_border(img: Image.Image, border_width: int = BORDER_WIDTH) -> Image.Image:
    """Add a white outline border around non-transparent pixels."""
    # Create mask from alpha channel
    alpha = img.split()[3]
    # Expand the mask
    expanded = alpha.filter(ImageFilter.MaxFilter(border_width * 2 + 1))

    # Create white border layer
    border_layer = Image.new("RGBA", img.size, (255, 255, 255, 0))
    border_pixels = border_layer.load()
    exp_pixels = expanded.load()
    alpha_pixels = alpha.load()

    for y in range(img.height):
        for x in range(img.width):
            if exp_pixels[x, y] > 0 and alpha_pixels[x, y] == 0:
                border_pixels[x, y] = (255, 255, 255, 255)

    # Composite: border behind original
    result = Image.alpha_composite(border_layer, img)
    return result


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
