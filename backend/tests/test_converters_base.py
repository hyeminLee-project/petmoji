"""converters/base.py 유닛 테스트"""
import base64
import io

import pytest
from PIL import Image

from app.converters.base import decode_image, encode_image, encode_gif


class TestDecodeImage:
    def test_valid_png_data_url(self, sample_image_b64: str):
        img = decode_image(sample_image_b64)
        assert isinstance(img, Image.Image)
        assert img.mode == "RGBA"
        assert img.size == (100, 100)

    def test_valid_jpeg_data_url(self):
        img = Image.new("RGB", (50, 50), (0, 128, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        data_url = f"data:image/jpeg;base64,{b64}"

        result = decode_image(data_url)
        assert isinstance(result, Image.Image)
        assert result.size == (50, 50)

    def test_non_data_url_raises(self):
        with pytest.raises(ValueError, match="URL-based"):
            decode_image("https://example.com/image.png")

    def test_plain_string_raises(self):
        with pytest.raises(ValueError):
            decode_image("not a valid image")


class TestEncodeImage:
    def test_returns_png_data_url(self):
        img = Image.new("RGBA", (32, 32), (0, 255, 0, 255))
        result = encode_image(img)
        assert result.startswith("data:image/png;base64,")

    def test_jpeg_format(self):
        img = Image.new("RGB", (32, 32), (0, 255, 0))
        result = encode_image(img, fmt="JPEG")
        assert result.startswith("data:image/jpeg;base64,")

    def test_roundtrip(self):
        original = Image.new("RGBA", (64, 64), (100, 150, 200, 255))
        encoded = encode_image(original)
        decoded = decode_image(encoded)
        assert decoded.size == original.size
        assert decoded.mode == "RGBA"


class TestEncodeGif:
    def test_returns_gif_data_url(self):
        frames = [
            Image.new("RGB", (32, 32), (255, 0, 0)),
            Image.new("RGB", (32, 32), (0, 255, 0)),
            Image.new("RGB", (32, 32), (0, 0, 255)),
        ]
        result = encode_gif(frames)
        assert result.startswith("data:image/gif;base64,")

    def test_valid_gif_with_frames(self):
        frames = [
            Image.new("RGB", (32, 32), (255, 0, 0)),
            Image.new("RGB", (32, 32), (0, 255, 0)),
        ]
        result = encode_gif(frames, duration=200)
        # GIF 디코딩해서 프레임 수 확인
        b64 = result.split(",", 1)[1]
        gif_bytes = base64.b64decode(b64)
        gif = Image.open(io.BytesIO(gif_bytes))
        assert gif.format == "GIF"
        assert gif.n_frames == 2
