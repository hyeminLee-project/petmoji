"""변환 포맷 레지스트리 — 포맷 메타데이터의 단일 진실 원천.

포맷 추가 시 이 파일의 FORMAT_REGISTRY에만 등록하면
/api/formats 응답, 변환 라우팅, 개수 제한, 프론트 목록이 모두 따라온다.
"""

from functools import partial

from app.converters.gif import convert_gif, convert_kakao_animated
from app.converters.imessage import convert_imessage
from app.converters.kakao import convert_kakao
from app.converters.kakao_submission import convert_kakao_submission
from app.converters.sticker import convert_sticker
from app.converters.wallpaper import convert_wallpaper

FORMAT_REGISTRY: dict[str, dict] = {
    "kakao": {
        "converter": convert_kakao,
        "name": "카카오톡 이모티콘",
        "icon": "💬",
        "size": "360x360",
        "limit": "150KB",
        "max_count": 32,
        "description": "360x360 (최대 32개)",
    },
    "kakao_animated": {
        "converter": convert_kakao_animated,
        "name": "카카오 움직이는 이모티콘",
        "icon": "💬",
        "size": "360x360",
        "limit": "650KB",
        "max_count": 24,
        "description": "360x360 GIF (최대 24개)",
    },
    "kakao_large_square": {
        "converter": partial(convert_kakao, variant="large_square"),
        "name": "카카오 큰이모티콘 (정사각)",
        "icon": "💬",
        "size": "540x540",
        "limit": "1MB",
        "max_count": 16,
        "description": "540x540 (최대 16개)",
    },
    "kakao_large_wide": {
        "converter": partial(convert_kakao, variant="large_wide"),
        "name": "카카오 큰이모티콘 (가로)",
        "icon": "💬",
        "size": "540x300",
        "limit": "1MB",
        "max_count": 16,
        "description": "540x300 (최대 16개)",
    },
    "kakao_large_tall": {
        "converter": partial(convert_kakao, variant="large_tall"),
        "name": "카카오 큰이모티콘 (세로)",
        "icon": "💬",
        "size": "300x540",
        "limit": "1MB",
        "max_count": 16,
        "description": "300x540 (최대 16개)",
    },
    "kakao_submission": {
        "converter": convert_kakao_submission,
        "name": "카카오 제안용 패키지",
        "icon": "📋",
        "size": "360x360",
        "limit": None,
        "max_count": 42,
        "description": "이모티콘+아이콘+공유 ZIP",
    },
    "imessage": {
        "converter": convert_imessage,
        "name": "iMessage 스티커",
        "icon": "🍎",
        "size": "408x408",
        "limit": None,
        "max_count": 16,
        "description": "408x408 스티커",
    },
    "sticker": {
        "converter": convert_sticker,
        "name": "투명 스티커 PNG",
        "icon": "✂️",
        "size": "512x512",
        "limit": None,
        "max_count": 16,
        "description": "512x512 투명 배경",
    },
    "gif": {
        "converter": convert_gif,
        "name": "움직이는 GIF",
        "icon": "🎬",
        "size": "256x256",
        "limit": None,
        "max_count": 16,
        "description": "256x256 감정 모션",
    },
    "wallpaper": {
        "converter": convert_wallpaper,
        "name": "폰 배경화면",
        "icon": "📱",
        "size": "1170x2532",
        "limit": None,
        "max_count": 16,
        "description": "1170x2532 패턴",
    },
}

CONVERTERS = {format_id: meta["converter"] for format_id, meta in FORMAT_REGISTRY.items()}

__all__ = ["CONVERTERS", "FORMAT_REGISTRY"]
