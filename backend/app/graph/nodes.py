"""LangGraph 위자드 노드 — 각 단계의 처리 로직."""

import logging

from app.graph.prompts import build_preview_prompt, build_wizard_prompt
from app.graph.state import WizardState
from app.services.analyzer import analyze_pet_photo
from app.services.generator import EMOTIONS, PROVIDERS

logger = logging.getLogger(__name__)


async def _generate_preview(state: WizardState) -> str:
    """현재 설정으로 미리보기 1장 생성."""
    prompt = build_preview_prompt(
        pet_features=state.get("pet_features", {}),
        style=state.get("style", "2d"),
        proportion=state.get("proportion", "chibi"),
        detail=state.get("detail"),
        reference=state.get("reference", "none"),
        custom_prompt=state.get("custom_prompt", ""),
    )
    generate_fn = PROVIDERS[state.get("provider", "gemini")]
    return await generate_fn(prompt)


async def analyze_node(state: WizardState) -> dict:
    """사진 분석 노드."""
    image_path = state["image_path"]
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    pet_features = await analyze_pet_photo(
        image_bytes,
        state.get("content_type", "image/jpeg"),
        state.get("analyzer", "gemini"),
    )

    return {
        "pet_features": pet_features.model_dump(),
        "current_step": "style",
    }


async def style_node(state: WizardState) -> dict:
    """스타일 선택 → 미리보기 생성."""
    preview_url = await _generate_preview(state)
    previews = state.get("previews", {})
    previews["style"] = preview_url

    return {
        "previews": previews,
        "current_step": "proportion",
    }


async def proportion_node(state: WizardState) -> dict:
    """비율 선택 → 미리보기 생성."""
    preview_url = await _generate_preview(state)
    previews = state.get("previews", {})
    previews["proportion"] = preview_url

    return {
        "previews": previews,
        "current_step": "detail",
    }


async def detail_node(state: WizardState) -> dict:
    """세부 조정 → 미리보기 생성."""
    preview_url = await _generate_preview(state)
    previews = state.get("previews", {})
    previews["detail"] = preview_url

    return {
        "previews": previews,
        "current_step": "reference",
    }


async def reference_node(state: WizardState) -> dict:
    """레퍼런스 선택 → 미리보기 생성."""
    preview_url = await _generate_preview(state)
    previews = state.get("previews", {})
    previews["reference"] = preview_url

    return {
        "previews": previews,
        "current_step": "generate",
    }


async def generate_node(state: WizardState) -> dict:
    """전체 이모지 세트 생성."""
    emoji_count = state.get("emoji_count", 8)
    generate_fn = PROVIDERS[state.get("provider", "gemini")]

    base_prompt = build_wizard_prompt(
        pet_features=state.get("pet_features", {}),
        style=state.get("style", "2d"),
        proportion=state.get("proportion", "chibi"),
        detail=state.get("detail"),
        reference=state.get("reference", "none"),
        custom_prompt=state.get("custom_prompt", ""),
    )

    emotions_to_generate = EMOTIONS[:emoji_count]
    emojis = []

    for emotion, description in emotions_to_generate:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

        image_url = await generate_fn(prompt)
        emojis.append({"emotion": emotion, "image_url": image_url})

    return {"emojis": emojis}


async def free_generate_node(state: WizardState) -> dict:
    """무료 티어: 분석 후 바로 4개 이모지 생성."""
    emoji_count = min(state.get("emoji_count", 4), 4)
    generate_fn = PROVIDERS[state.get("provider", "gemini")]

    base_prompt = build_wizard_prompt(
        pet_features=state.get("pet_features", {}),
        style=state.get("style", "2d"),
        proportion="chibi",
    )

    emotions_to_generate = EMOTIONS[:emoji_count]
    emojis = []

    for emotion, description in emotions_to_generate:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

        image_url = await generate_fn(prompt)
        emojis.append({"emotion": emotion, "image_url": image_url})

    return {"emojis": emojis}
