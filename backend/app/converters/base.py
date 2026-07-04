import base64
import io

from PIL import Image


def decode_image(image_url: str) -> Image.Image:
    """Decode a base64 data URL or load from URL into a PIL Image."""
    if image_url.startswith("data:"):
        # data:image/png;base64,xxxxx
        header, b64_data = image_url.split(",", 1)
        image_bytes = base64.b64decode(b64_data)
    else:
        raise ValueError("URL-based images not supported yet, only base64 data URLs")

    return Image.open(io.BytesIO(image_bytes)).convert("RGBA")


def encode_image(image: Image.Image, fmt: str = "PNG") -> str:
    """Encode a PIL Image to a base64 data URL."""
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    mime = f"image/{fmt.lower()}"
    return f"data:{mime};base64,{b64}"


def encode_gif(frames: list[Image.Image], duration: int = 500, transparent: bool = False) -> str:
    """Encode PIL Image frames to an animated GIF base64 data URL.

    transparent=True면 RGBA 프레임의 알파를 GIF 투명 인덱스(255)로 변환한다.
    """
    if transparent:
        converted = []
        for frame in frames:
            if frame.mode != "RGBA":
                frame = frame.convert("RGBA")
            alpha = frame.getchannel("A")
            # 팔레트 0~254 사용, 255는 투명 인덱스로 예약
            p = frame.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255)
            mask = alpha.point(lambda a: 255 if a <= 128 else 0)
            p.paste(255, mask)
            converted.append(p)
        frames = converted

    buffer = io.BytesIO()
    save_kwargs: dict = {
        "format": "GIF",
        "save_all": True,
        "append_images": frames[1:],
        "duration": duration,
        "loop": 0,
        "disposal": 2,
    }
    if transparent:
        save_kwargs["transparency"] = 255
    frames[0].save(buffer, **save_kwargs)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/gif;base64,{b64}"
