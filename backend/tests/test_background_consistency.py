"""배경 키 일관성 검증 테스트.

PLAIN_BACKGROUNDS에 속하지 않는 배경은 반드시 장면 설명(BACKGROUND_DESCRIPTIONS)을 가져야 한다.
새 배경을 추가할 때 한쪽만 수정하면 이 테스트가 실패하여 불일치를 방지한다.
"""

from app.models.tiers import BACKGROUNDS
from app.services.generator import BACKGROUND_DESCRIPTIONS, PLAIN_BACKGROUNDS


def test_all_backgrounds_have_descriptions():
    """티어에 정의된 모든 배경이 BACKGROUND_DESCRIPTIONS에 존재해야 한다."""
    for bg in BACKGROUNDS:
        assert bg in BACKGROUND_DESCRIPTIONS, (
            f"배경 '{bg}'가 BACKGROUNDS에는 있지만 BACKGROUND_DESCRIPTIONS에 없음"
        )


def test_plain_backgrounds_are_subset_of_descriptions():
    """PLAIN_BACKGROUNDS의 모든 값이 BACKGROUND_DESCRIPTIONS에 존재해야 한다."""
    for bg in PLAIN_BACKGROUNDS:
        assert bg in BACKGROUND_DESCRIPTIONS, (
            f"PLAIN_BACKGROUNDS '{bg}'가 BACKGROUND_DESCRIPTIONS에 없음"
        )


def test_scene_backgrounds_have_descriptions():
    """PLAIN이 아닌 배경은 반드시 장면 설명을 가져야 한다."""
    scene_backgrounds = set(BACKGROUND_DESCRIPTIONS.keys()) - set(PLAIN_BACKGROUNDS)
    for bg in scene_backgrounds:
        desc = BACKGROUND_DESCRIPTIONS[bg]
        assert desc, f"장면 배경 '{bg}'의 설명이 비어있음"
