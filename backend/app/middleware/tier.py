"""티어 검증 FastAPI dependency."""

from fastapi import HTTPException, Query

from app.models.tiers import TIER_CONFIG, TierType


def get_tier(tier: TierType = Query("free")) -> dict:
    """요청에서 티어를 추출하고 설정 반환."""
    if tier not in TIER_CONFIG:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 티어: {tier}")
    return {"tier": tier, "config": TIER_CONFIG[tier]}


def require_wizard(tier_info: dict = None) -> dict:
    """위자드 접근 가능 여부 검증."""
    if tier_info is None or not tier_info["config"].get("guided_wizard"):
        raise HTTPException(
            status_code=403,
            detail="위자드는 프리미엄 이상 티어에서 사용 가능합니다",
        )
    return tier_info
