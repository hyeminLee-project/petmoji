from functools import partial

from app.converters.gif import convert_gif, convert_kakao_animated
from app.converters.imessage import convert_imessage
from app.converters.kakao import convert_kakao
from app.converters.sticker import convert_sticker
from app.converters.wallpaper import convert_wallpaper

CONVERTERS = {
    "kakao": convert_kakao,
    "kakao_animated": convert_kakao_animated,
    "kakao_large_square": partial(convert_kakao, variant="large_square"),
    "kakao_large_wide": partial(convert_kakao, variant="large_wide"),
    "kakao_large_tall": partial(convert_kakao, variant="large_tall"),
    "imessage": convert_imessage,
    "sticker": convert_sticker,
    "gif": convert_gif,
    "wallpaper": convert_wallpaper,
}

__all__ = ["CONVERTERS"]
