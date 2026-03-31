"""확장 프롬프트 빌더 — 5 스타일, 3 비율, 세부 조정, 레퍼런스."""

from app.services.generator import _sanitize_custom_prompt

STYLE_DESCRIPTIONS = {
    "2d": "clean 2D vector art style, flat colors, bold outlines, like Kakao Friends or LINE stickers",
    "3d": "cute 3D rendered style, soft lighting, clay/vinyl figure look, like Pop Mart figurines",
    "watercolor": "soft watercolor painting style, gentle brush strokes, pastel colors, dreamy atmosphere",
    "pixel": "pixel art style, 32x32 retro game character, limited color palette, crisp edges",
    "realistic": "photorealistic digital painting, real fur texture, natural proportions, studio lighting",
}

PROPORTION_DESCRIPTIONS = {
    "chibi": "chibi-proportioned (very big head, tiny body, 2:1 head-to-body ratio)",
    "normal": "standard cartoon proportions (slightly big head, 3:1 head-to-body ratio)",
    "realistic": "natural body proportions, anatomically accurate",
}

DETAIL_DEFAULTS = {
    "eye_size": "big",
    "outline": "bold",
    "background": "white",
}

REFERENCE_DESCRIPTIONS = {
    "kakao": "in the style of Kakao Friends characters (Ryan, Apeach, Muzi) — simple shapes, minimal detail, round forms, very cute",
    "line": "in the style of LINE Friends characters (Brown, Cony, Sally) — clean outlines, expressive faces, iconic poses",
    "sanrio": "in the style of Sanrio characters (Hello Kitty, My Melody) — extremely cute, pastel colors, bow accessories, kawaii aesthetic",
    "popmart": "in the style of Pop Mart designer toys — glossy finish, collectible figure look, stylized proportions",
    "none": "",
}


def build_wizard_prompt(
    pet_features: dict,
    style: str = "2d",
    proportion: str = "chibi",
    detail: dict | None = None,
    reference: str = "none",
    custom_prompt: str = "",
) -> str:
    """위자드 설정을 기반으로 캐릭터 프롬프트 생성."""
    detail = detail or DETAIL_DEFAULTS

    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["2d"])
    proportion_desc = PROPORTION_DESCRIPTIONS.get(proportion, PROPORTION_DESCRIPTIONS["chibi"])
    reference_desc = REFERENCE_DESCRIPTIONS.get(reference, "")

    eye_desc = {
        "big": "very large, sparkly eyes",
        "normal": "medium-sized eyes",
        "small": "small, detailed eyes",
    }.get(detail.get("eye_size", "big"), "large eyes")

    outline_desc = {
        "bold": "thick bold outlines",
        "normal": "medium outlines",
        "none": "no outlines, smooth edges",
    }.get(detail.get("outline", "bold"), "bold outlines")

    bg_desc = {
        "white": "pure white background",
        "transparent": "transparent background",
        "gradient": "soft pastel gradient background",
    }.get(detail.get("background", "white"), "white background")

    # 기본 캐릭터 설명
    features = pet_features
    base = f"""A cute character based on a {features.get("animal_type", "pet")} ({features.get("breed", "mixed")}).
Physical traits: {features.get("fur_color", "")} {features.get("fur_pattern", "")} fur, {features.get("ear_shape", "")} ears, {features.get("eye_shape", "")} {features.get("eye_color", "")} eyes, {features.get("nose_shape", "")} nose, {features.get("body_shape", "")} body.
Distinctive features: {", ".join(features.get("distinctive_features", []))}.
Style: {style_desc}.
Proportions: {proportion_desc}.
Eyes: {eye_desc}. Lines: {outline_desc}.
Background: {bg_desc}.
The character should be centered, emoji-sized square composition."""

    if reference_desc:
        base += f"\nReference: {reference_desc}."

    sanitized = _sanitize_custom_prompt(custom_prompt)
    if sanitized:
        base += f"\nAdditional instructions: {sanitized}"

    return base


def build_preview_prompt(pet_features: dict, **kwargs) -> str:
    """미리보기용 프롬프트 (중립 표정)."""
    base = build_wizard_prompt(pet_features, **kwargs)
    return f"""{base}
Expression/pose: neutral, standing, looking at camera.
No text, no watermark."""
