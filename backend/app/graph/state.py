"""LangGraph 위자드 상태 정의."""

from typing import Literal, TypedDict


class WizardState(TypedDict, total=False):
    # 세션 ID
    session_id: str
    tier: Literal["free", "premium", "custom"]

    # 반려동물 분석 결과
    pet_features: dict  # PetFeatures as dict

    # 이미지 정보 (파일 경로로 저장, state에 bytes 넣지 않음)
    image_path: str
    content_type: str

    # 위자드 선택값 (단계별 누적)
    style: str  # 2d, 3d, watercolor, pixel, realistic
    proportion: str  # chibi, normal, realistic
    detail: dict  # {"eye_size": "big", "outline": "bold", "background": "white"}
    reference: str  # kakao, line, sanrio, popmart, none
    custom_prompt: str  # custom 티어 전용

    # 장면 설정 (악세사리, 배경, 시간대)
    accessory: str  # none, ribbon, bowtie, crown, ...
    scene_background: str  # white, park, room, cafe, ...
    time_of_day: str  # none, morning, afternoon, sunset, night

    # 단계 추적
    current_step: Literal["upload", "style", "proportion", "detail", "reference", "generate"]

    # 미리보기 이미지 (단계별)
    previews: dict  # {"style": "data:image/png;base64,...", ...}

    # 최종 결과
    emojis: list[dict]

    # AI 설정
    provider: str  # openai, gemini
    analyzer: str  # anthropic, gemini
    emoji_count: int
