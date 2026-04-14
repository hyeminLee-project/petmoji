"""티어 시스템 설정."""

from typing import Literal

TierType = Literal["free", "premium", "custom"]

ACCESSORIES = [
    "none",
    "ribbon",
    "bowtie",
    "crown",
    "flower",
    "glasses",
    "hat",
    "scarf",
    "bandana",
    "headband",
]

BACKGROUNDS = [
    "white",
    "transparent",
    "gradient",
    "park",
    "room",
    "cafe",
    "beach",
    "snow",
    "sky",
    "night",
]

TIME_OF_DAY = ["none", "morning", "afternoon", "sunset", "night"]

TIER_CONFIG = {
    "free": {
        "styles": ["2d", "3d"],
        "max_emotions": 4,
        "guided_wizard": False,
        "custom_prompt": False,
        "accessories": ["none"],
        "backgrounds": ["white", "transparent"],
        "time_of_day": ["none"],
        "formats": ["png"],
        "regeneration_limit": 1,
    },
    "premium": {
        "styles": ["2d", "3d", "watercolor", "pixel", "realistic"],
        "max_emotions": 16,
        "guided_wizard": True,
        "custom_prompt": False,
        "accessories": ACCESSORIES,
        "backgrounds": BACKGROUNDS,
        "time_of_day": TIME_OF_DAY,
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
        "accessories": ACCESSORIES,
        "backgrounds": BACKGROUNDS,
        "time_of_day": TIME_OF_DAY,
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
