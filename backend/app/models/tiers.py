"""티어 시스템 설정."""

from typing import Literal

TierType = Literal["free", "premium", "custom"]

TIER_CONFIG = {
    "free": {
        "styles": ["2d", "3d"],
        "max_emotions": 4,
        "guided_wizard": False,
        "custom_prompt": False,
        "formats": ["png"],
        "regeneration_limit": 1,
    },
    "premium": {
        "styles": ["2d", "3d", "watercolor", "pixel", "realistic"],
        "max_emotions": 16,
        "guided_wizard": True,
        "custom_prompt": False,
        "formats": [
            "png",
            "kakao",
            "kakao_large_square",
            "kakao_large_wide",
            "kakao_large_tall",
            "imessage",
            "sticker",
            "gif",
            "wallpaper",
        ],
        "regeneration_limit": 3,
    },
    "custom": {
        "styles": ["2d", "3d", "watercolor", "pixel", "realistic"],
        "max_emotions": 16,
        "guided_wizard": True,
        "custom_prompt": True,
        "formats": [
            "png",
            "kakao",
            "kakao_large_square",
            "kakao_large_wide",
            "kakao_large_tall",
            "imessage",
            "sticker",
            "gif",
            "wallpaper",
        ],
        "regeneration_limit": -1,  # unlimited
    },
}


def get_tier_config(tier: TierType) -> dict:
    """티어별 설정 반환."""
    return TIER_CONFIG[tier]
