from app.converters.kakao import convert_kakao
from app.converters.imessage import convert_imessage
from app.converters.sticker import convert_sticker
from app.converters.gif import convert_gif
from app.converters.wallpaper import convert_wallpaper

CONVERTERS = {
    "kakao": convert_kakao,
    "imessage": convert_imessage,
    "sticker": convert_sticker,
    "gif": convert_gif,
    "wallpaper": convert_wallpaper,
}

__all__ = ["CONVERTERS"]
