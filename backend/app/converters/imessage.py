"""iMessage 스티커 규격 변환기.

Apple iMessage 스티커 규격:
- Small: 300x300px
- Medium: 408x408px
- Large: 618x618px
- PNG, 투명 배경
"""

from PIL import Image

from app.converters.base import decode_image, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

IMESSAGE_SIZE = (408, 408)  # Medium


def convert_imessage(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """Convert emoji set to iMessage sticker format (Medium)."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)

        img.thumbnail(IMESSAGE_SIZE, Image.LANCZOS)
        canvas = Image.new("RGBA", IMESSAGE_SIZE, (0, 0, 0, 0))
        offset = (
            (IMESSAGE_SIZE[0] - img.width) // 2,
            (IMESSAGE_SIZE[1] - img.height) // 2,
        )
        canvas.paste(img, offset, img)

        results.append(ConvertedEmoji(
            emotion=emoji.emotion,
            image_url=encode_image(canvas),
            format="imessage",
            width=IMESSAGE_SIZE[0],
            height=IMESSAGE_SIZE[1],
        ))

    return results
