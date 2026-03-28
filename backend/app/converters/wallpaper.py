"""폰 배경화면 변환기.

이모지를 반복 패턴으로 배치한 스마트폰 배경화면 생성.
"""

from PIL import Image

from app.converters.base import decode_image, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

# iPhone 기준 배경화면 사이즈
WALLPAPER_SIZE = (1170, 2532)
EMOJI_TILE_SIZE = (180, 180)
PADDING = 20
BG_COLOR = (255, 248, 240, 255)  # 따뜻한 크림색


def convert_wallpaper(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """Create a phone wallpaper with emoji pattern grid."""
    # 이모지 이미지들을 미리 로드하고 리사이즈
    tiles: list[tuple[str, Image.Image]] = []
    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(EMOJI_TILE_SIZE, Image.LANCZOS)
        tiles.append((emoji.emotion, img))

    if not tiles:
        return []

    # 배경화면 캔버스
    wallpaper = Image.new("RGBA", WALLPAPER_SIZE, BG_COLOR)

    # 격자 배치
    cols = (WALLPAPER_SIZE[0] - PADDING) // (EMOJI_TILE_SIZE[0] + PADDING)
    rows = (WALLPAPER_SIZE[1] - PADDING) // (EMOJI_TILE_SIZE[1] + PADDING)

    # 좌우 중앙 정렬을 위한 시작 오프셋
    total_width = cols * (EMOJI_TILE_SIZE[0] + PADDING) - PADDING
    x_start = (WALLPAPER_SIZE[0] - total_width) // 2

    tile_index = 0
    for row in range(rows):
        # 홀수 행은 반칸 오프셋 (벌집 패턴)
        row_offset = (EMOJI_TILE_SIZE[0] + PADDING) // 2 if row % 2 == 1 else 0

        for col in range(cols):
            x = x_start + col * (EMOJI_TILE_SIZE[0] + PADDING) + row_offset
            y = PADDING + row * (EMOJI_TILE_SIZE[1] + PADDING)

            if x + EMOJI_TILE_SIZE[0] > WALLPAPER_SIZE[0]:
                continue

            _, tile_img = tiles[tile_index % len(tiles)]
            # 타일 중앙 정렬
            paste_x = x + (EMOJI_TILE_SIZE[0] - tile_img.width) // 2
            paste_y = y + (EMOJI_TILE_SIZE[1] - tile_img.height) // 2
            wallpaper.paste(tile_img, (paste_x, paste_y), tile_img)
            tile_index += 1

    return [ConvertedEmoji(
        emotion="wallpaper",
        image_url=encode_image(wallpaper),
        format="wallpaper",
        width=WALLPAPER_SIZE[0],
        height=WALLPAPER_SIZE[1],
    )]
