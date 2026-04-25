"""Agent 툴 정의 — 기존 서비스를 Claude tool_use JSON schema + dispatcher로 래핑."""

import json
import logging

from app.converters.kakao import convert_kakao
from app.services.analyzer import analyze_pet_photo
from app.services.generator import EMOTIONS, generate_emoji_set

logger = logging.getLogger(__name__)

# ── Claude tool_use JSON schema 정의 ─────────────────────────

TOOLS = [
    {
        "name": "analyze_pet",
        "description": (
            "반려동물 사진을 분석하여 종, 품종, 털색, 체형 등 특징을 추출한다. "
            "이모지 생성 전에 반드시 먼저 호출해야 한다. "
            "사진은 세션에 이미 업로드되어 있으므로 별도 인자 불필요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "analyzer": {
                    "type": "string",
                    "enum": ["gemini", "anthropic"],
                    "description": "분석 엔진. 기본값 gemini.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "generate_emojis",
        "description": (
            "추출된 펫 특징으로 이모지 이미지 세트를 생성한다. "
            "analyze_pet으로 특징을 먼저 추출한 뒤 호출해야 한다. "
            "감정별 이미지를 병렬로 생성하며, 캡션이 자동으로 오버레이된다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["2d", "3d", "watercolor", "pixel", "realistic"],
                    "description": "이모지 스타일. 기본값 2d.",
                },
                "emoji_count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 32,
                    "description": "생성할 이모지 수. 기본값 8.",
                },
                "provider": {
                    "type": "string",
                    "enum": ["openai", "gemini"],
                    "description": "이미지 생성 엔진. 기본값 gemini.",
                },
                "accessory": {
                    "type": "string",
                    "enum": [
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
                    ],
                    "description": "캐릭터 악세사리. 기본값 none.",
                },
                "background": {
                    "type": "string",
                    "enum": [
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
                    ],
                    "description": "배경. 기본값 white.",
                },
                "time_of_day": {
                    "type": "string",
                    "enum": ["none", "morning", "afternoon", "sunset", "night"],
                    "description": "시간대 조명. 기본값 none.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "convert_kakao",
        "description": (
            "생성된 이모지를 카카오 이모티콘 규격으로 변환한다. "
            "generate_emojis로 이모지를 먼저 생성한 뒤 호출해야 한다. "
            "사용자가 '카카오' 포맷을 요청했을 때만 호출한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "variant": {
                    "type": "string",
                    "enum": ["standard", "large_square", "large_wide", "large_tall"],
                    "description": (
                        "카카오 이모티콘 규격. "
                        "standard=360x360, large_square=540x540, "
                        "large_wide=540x300, large_tall=300x540. "
                        "기본값 standard."
                    ),
                },
            },
            "required": [],
        },
    },
]

# 사용 가능한 감정 목록 (시스템 프롬프트에 포함할 참고 정보)
AVAILABLE_EMOTIONS = [name for name, _ in EMOTIONS]


# ── Dispatcher: 툴 이름 → 서비스 함수 호출 ──────────────────


async def execute_tool(name: str, tool_input: dict, context: dict) -> str:
    """Claude가 호출한 툴을 실제 서비스로 연결하고 결과를 JSON 문자열로 반환."""

    if name == "analyze_pet":
        if "image_bytes" not in context:
            return json.dumps({"error": "이미지가 업로드되지 않았습니다"})

        analyzer = tool_input.get("analyzer", "gemini")
        features = await analyze_pet_photo(
            context["image_bytes"], context["content_type"], analyzer
        )
        context["features"] = features
        return json.dumps(
            {
                "success": True,
                "features": features.model_dump(),
            },
            ensure_ascii=False,
        )

    elif name == "generate_emojis":
        if "features" not in context:
            return json.dumps({"error": "먼저 analyze_pet을 호출하여 특징을 추출하세요"})

        results = await generate_emoji_set(
            features=context["features"],
            style=tool_input.get("style", "2d"),
            emoji_count=tool_input.get("emoji_count", 8),
            provider=tool_input.get("provider", "gemini"),
            accessory=tool_input.get("accessory", "none"),
            background=tool_input.get("background", "white"),
            time_of_day=tool_input.get("time_of_day", "none"),
        )
        context["emojis"] = results
        return json.dumps(
            {
                "success": True,
                "count": len(results),
                "emotions": [r.emotion for r in results],
            },
            ensure_ascii=False,
        )

    elif name == "convert_kakao":
        if "emojis" not in context:
            return json.dumps({"error": "먼저 generate_emojis를 호출하여 이모지를 생성하세요"})

        variant = tool_input.get("variant", "standard")
        converted = convert_kakao(context["emojis"], variant)
        context["converted"] = converted
        return json.dumps(
            {
                "success": True,
                "count": len(converted),
                "format": f"kakao_{variant}",
            },
            ensure_ascii=False,
        )

    else:
        return json.dumps({"error": f"알 수 없는 툴: {name}"})
