"""카카오 이모티콘 스토어 제안용 패키지 생성기.

멈춰있는 이모티콘 제안 패키지:
- 이모티콘 32개: PNG, 360x360, 150KB 이하, 투명 배경
- 아이콘 1개: PNG, 78x78, 16KB 이하
- 공유 이미지 1개: PNG, 600x166, 500KB 이하
"""

import base64
import io
import zipfile

from PIL import Image

from app.converters.base import decode_image
from app.converters.kakao import _fit_to_canvas, _optimize_size
from app.models.schemas import ConvertedEmoji, EmojiResult

ICON_SIZE = (78, 78)
ICON_MAX_BYTES = 16 * 1024
SHARE_SIZE = (600, 166)
SHARE_MAX_BYTES = 500 * 1024
EMOTICON_SIZE = (360, 360)
EMOTICON_MAX_BYTES = 150 * 1024


def _create_icon(img: Image.Image) -> bytes:
    """대표 이모지로 78x78 아이콘 생성."""
    icon = img.copy()
    icon.thumbnail(ICON_SIZE, Image.LANCZOS)

    canvas = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
    offset = (
        (ICON_SIZE[0] - icon.width) // 2,
        (ICON_SIZE[1] - icon.height) // 2,
    )
    canvas.paste(icon, offset, icon)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", dpi=(72, 72), optimize=True)

    if buf.tell() > ICON_MAX_BYTES:
        scale = 0.8
        for _ in range(5):
            new_size = (int(canvas.width * scale), int(canvas.height * scale))
            resized = canvas.resize(new_size, Image.LANCZOS)
            padded = Image.new("RGBA", ICON_SIZE, (0, 0, 0, 0))
            off = ((ICON_SIZE[0] - resized.width) // 2, (ICON_SIZE[1] - resized.height) // 2)
            padded.paste(resized, off, resized)
            buf = io.BytesIO()
            padded.save(buf, format="PNG", dpi=(72, 72), optimize=True)
            if buf.tell() <= ICON_MAX_BYTES:
                break
            scale -= 0.1

    return buf.getvalue()


def _create_share_image(images: list[Image.Image]) -> bytes:
    """대표 이모지 2~3개로 600x166 공유 이미지 생성."""
    canvas = Image.new("RGBA", SHARE_SIZE, (255, 255, 255, 0))

    preview_images = images[:3]
    count = len(preview_images)
    thumb_h = SHARE_SIZE[1] - 20
    total_width = 0
    thumbs = []

    for img in preview_images:
        thumb = img.copy()
        thumb.thumbnail((thumb_h, thumb_h), Image.LANCZOS)
        thumbs.append(thumb)
        total_width += thumb.width

    spacing = (SHARE_SIZE[0] - total_width) // (count + 1)
    x = spacing

    for thumb in thumbs:
        y = (SHARE_SIZE[1] - thumb.height) // 2
        canvas.paste(thumb, (x, y), thumb)
        x += thumb.width + spacing

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", dpi=(72, 72), optimize=True)
    return buf.getvalue()


def convert_kakao_submission(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """카카오 제안 패키지 ZIP 생성.

    Returns:
        단일 ConvertedEmoji (ZIP 파일을 base64로 인코딩)
    """
    decoded_images: list[Image.Image] = []
    emoticon_pngs: list[tuple[str, bytes]] = []

    for i, emoji in enumerate(emojis):
        img = decode_image(emoji.image_url)
        decoded_images.append(img)

        canvas = _fit_to_canvas(img, EMOTICON_SIZE)
        optimized_url = _optimize_size(canvas, EMOTICON_MAX_BYTES)
        _, b64_data = optimized_url.split(",", 1)
        png_bytes = base64.b64decode(b64_data)

        filename = f"{i + 1:02d}_{emoji.emotion}.png"
        emoticon_pngs.append((filename, png_bytes))

    icon_bytes = _create_icon(decoded_images[0])
    share_bytes = _create_share_image(decoded_images)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, png_data in emoticon_pngs:
            zf.writestr(f"emoticons/{filename}", png_data)
        zf.writestr("icon_78x78.png", icon_bytes)
        zf.writestr("share_600x166.png", share_bytes)

    zip_b64 = base64.b64encode(zip_buf.getvalue()).decode("utf-8")

    return [
        ConvertedEmoji(
            emotion="package",
            image_url=f"data:application/zip;base64,{zip_b64}",
            format="kakao_submission",
            width=360,
            height=360,
        )
    ]
