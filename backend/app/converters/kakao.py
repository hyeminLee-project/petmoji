"""카카오톡 이모티콘 규격 변환기.

카카오톡 이모티콘 규격:
- 메인 이모티콘: 360x360px
- 탭 아이콘: 80x80px
- PNG, 투명 배경 권장
"""

from PIL import Image

from app.converters.base import decode_image, encode_image
from app.models.schemas import ConvertedEmoji, EmojiResult

KAKAO_MAIN_SIZE = (360, 360)
KAKAO_TAB_SIZE = (80, 80)


def convert_kakao(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """Convert emoji set to Kakao emoticon format."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)

        # 메인 이모티콘 (360x360)
        main_img = img.copy()
        main_img.thumbnail(KAKAO_MAIN_SIZE, Image.LANCZOS)
        # 중앙 정렬로 360x360 캔버스에 배치
        canvas = Image.new("RGBA", KAKAO_MAIN_SIZE, (0, 0, 0, 0))
        offset = (
            (KAKAO_MAIN_SIZE[0] - main_img.width) // 2,
            (KAKAO_MAIN_SIZE[1] - main_img.height) // 2,
        )
        canvas.paste(main_img, offset, main_img)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=encode_image(canvas),
                format="kakao",
                width=KAKAO_MAIN_SIZE[0],
                height=KAKAO_MAIN_SIZE[1],
            )
        )

    return results
