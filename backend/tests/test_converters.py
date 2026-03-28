"""5개 converter 유닛 테스트"""
import base64
import io

from PIL import Image

from app.converters.kakao import convert_kakao
from app.converters.imessage import convert_imessage
from app.converters.sticker import convert_sticker
from app.converters.gif import convert_gif
from app.converters.wallpaper import convert_wallpaper
from app.models.schemas import EmojiResult


class TestKakaoConverter:
    def test_output_count(self, sample_emojis: list[EmojiResult]):
        result = convert_kakao(sample_emojis)
        assert len(result) == 2

    def test_dimensions(self, sample_emojis: list[EmojiResult]):
        result = convert_kakao(sample_emojis)
        for emoji in result:
            assert emoji.format == "kakao"
            assert emoji.width == 360
            assert emoji.height == 360

    def test_output_is_png(self, sample_emojis: list[EmojiResult]):
        result = convert_kakao(sample_emojis)
        assert result[0].image_url.startswith("data:image/png;base64,")

    def test_empty_input(self):
        assert convert_kakao([]) == []


class TestImessageConverter:
    def test_output_count(self, sample_emojis: list[EmojiResult]):
        result = convert_imessage(sample_emojis)
        assert len(result) == 2

    def test_dimensions(self, sample_emojis: list[EmojiResult]):
        result = convert_imessage(sample_emojis)
        for emoji in result:
            assert emoji.format == "imessage"
            assert emoji.width == 408
            assert emoji.height == 408

    def test_empty_input(self):
        assert convert_imessage([]) == []


class TestStickerConverter:
    def test_output_count(self, sample_emojis: list[EmojiResult]):
        result = convert_sticker(sample_emojis)
        assert len(result) == 2

    def test_dimensions(self, sample_emojis: list[EmojiResult]):
        result = convert_sticker(sample_emojis)
        for emoji in result:
            assert emoji.format == "sticker"
            assert emoji.width == 512
            assert emoji.height == 512

    def test_empty_input(self):
        assert convert_sticker([]) == []


class TestGifConverter:
    def test_output_count(self, sample_emojis: list[EmojiResult]):
        result = convert_gif(sample_emojis)
        assert len(result) == 2

    def test_dimensions(self, sample_emojis: list[EmojiResult]):
        result = convert_gif(sample_emojis)
        for emoji in result:
            assert emoji.format == "gif"
            assert emoji.width == 256
            assert emoji.height == 256

    def test_output_is_gif(self, sample_emojis: list[EmojiResult]):
        result = convert_gif(sample_emojis)
        assert result[0].image_url.startswith("data:image/gif;base64,")

    def test_has_multiple_frames(self, sample_emojis: list[EmojiResult]):
        result = convert_gif(sample_emojis)
        b64 = result[0].image_url.split(",", 1)[1]
        gif = Image.open(io.BytesIO(base64.b64decode(b64)))
        assert gif.n_frames > 1

    def test_empty_input(self):
        assert convert_gif([]) == []


class TestWallpaperConverter:
    def test_returns_single_item(self, sample_emojis: list[EmojiResult]):
        result = convert_wallpaper(sample_emojis)
        assert len(result) == 1

    def test_dimensions(self, sample_emojis: list[EmojiResult]):
        result = convert_wallpaper(sample_emojis)
        assert result[0].format == "wallpaper"
        assert result[0].width == 1170
        assert result[0].height == 2532

    def test_emotion_label(self, sample_emojis: list[EmojiResult]):
        result = convert_wallpaper(sample_emojis)
        assert result[0].emotion == "wallpaper"

    def test_empty_input(self):
        assert convert_wallpaper([]) == []
