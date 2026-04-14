import base64
import logging

from app.models.schemas import EmojiResult, PetFeatures

logger = logging.getLogger(__name__)

EMOTIONS = [
    ("happy", "smiling big with sparkly eyes, tail wagging"),
    ("sad", "teary eyes, droopy ears, looking down"),
    ("angry", "puffed cheeks, furrowed brows, tiny flames"),
    ("sleepy", "half-closed eyes, yawning, zzz floating"),
    ("love", "heart eyes, blushing cheeks, hearts floating around"),
    ("surprised", "wide open eyes and mouth, exclamation mark"),
    ("cool", "wearing tiny sunglasses, confident smirk"),
    ("celebrate", "party hat, confetti, jumping with joy"),
]


PROMPT_BLOCKLIST = [
    "ignore previous",
    "ignore above",
    "disregard",
    "forget your instructions",
    "system prompt",
    "you are now",
    "act as",
    "pretend to be",
    "override",
    "jailbreak",
    "nsfw",
    "nude",
    "naked",
    "violent",
    "gore",
    "weapon",
    "drug",
    "explicit",
]


def _sanitize_custom_prompt(prompt: str) -> str:
    """커스텀 프롬프트에서 위험한 패턴 제거."""
    lower = prompt.lower()
    for blocked in PROMPT_BLOCKLIST:
        if blocked in lower:
            return ""
    return prompt


STYLE_DESCRIPTIONS = {
    "2d": "clean 2D vector art style, flat colors, bold outlines, like Kakao Friends or LINE stickers",
    "3d": "cute 3D rendered style, soft lighting, clay/vinyl figure look, like Pop Mart figurines",
    "watercolor": "soft watercolor painting style, gentle brushstrokes, pastel tones",
    "pixel": "retro pixel art style, 16-bit game aesthetic, crisp pixels",
    "realistic": "semi-realistic illustration style, detailed fur textures, soft shading",
}

ACCESSORY_DESCRIPTIONS = {
    "none": "",
    "ribbon": "wearing a cute ribbon on head",
    "bowtie": "wearing a small bowtie around neck",
    "crown": "wearing a tiny golden crown",
    "flower": "with a flower tucked behind one ear",
    "glasses": "wearing small round glasses",
    "hat": "wearing a cute bucket hat",
    "scarf": "wearing a cozy knit scarf",
    "bandana": "wearing a patterned bandana",
    "headband": "wearing a cute headband with ears",
}

BACKGROUND_DESCRIPTIONS = {
    "white": "on a clean white background",
    "transparent": "on a clean white background",
    "gradient": "on a soft pastel gradient background",
    "park": "in a sunny green park with trees",
    "room": "in a cozy living room with warm lighting",
    "cafe": "sitting in a cute cafe with coffee cups",
    "beach": "on a sandy beach with gentle waves",
    "snow": "in a snowy winter wonderland",
    "sky": "floating among fluffy clouds in a blue sky",
    "night": "under a starry night sky with moon",
}

TIME_DESCRIPTIONS = {
    "none": "",
    "morning": "in warm golden morning light",
    "afternoon": "in bright daylight",
    "sunset": "bathed in warm orange sunset glow",
    "night": "under soft moonlight with a dark sky",
}


def _build_character_prompt(
    features: PetFeatures,
    style: str,
    custom_prompt: str = "",
    accessory: str = "none",
    background: str = "white",
    time_of_day: str = "none",
) -> str:
    """Build the base character description from pet features."""
    style_desc = STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS["2d"])

    base = f"""A cute character based on a {features.animal_type} ({features.breed}).
Physical traits: {features.fur_color} {features.fur_pattern} fur, {features.ear_shape} ears, {features.eye_shape} {features.eye_color} eyes, {features.nose_shape} nose, {features.body_shape} body.
Distinctive features: {", ".join(features.distinctive_features)}.
Style: {style_desc}.
The character should be chibi-proportioned (big head, small body), centered, emoji-sized square composition."""

    # 악세사리
    acc_desc = ACCESSORY_DESCRIPTIONS.get(accessory, "")
    if acc_desc:
        base += f"\nAccessory: {acc_desc}."

    # 배경
    bg_desc = BACKGROUND_DESCRIPTIONS.get(background, BACKGROUND_DESCRIPTIONS["white"])
    base += f"\nBackground: {bg_desc}."

    # 시간대
    time_desc = TIME_DESCRIPTIONS.get(time_of_day, "")
    if time_desc:
        base += f"\nLighting: {time_desc}."

    sanitized = _sanitize_custom_prompt(custom_prompt)
    if sanitized:
        base += f"\nAdditional instructions: {sanitized}"

    return base


async def _generate_with_openai(prompt: str) -> str:
    """Generate image using GPT-4o (OpenAI)."""
    from openai import OpenAI

    client = OpenAI()
    response = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="medium",
    )

    image_b64 = response.data[0].b64_json
    if not image_b64:
        image_url = response.data[0].url or ""
    else:
        image_url = f"data:image/png;base64,{image_b64}"

    return image_url


async def _generate_with_gemini(prompt: str) -> str:
    """Generate image using Gemini Imagen 3."""
    from google import genai
    from google.genai import types

    client = genai.Client()
    response = client.models.generate_images(
        model="imagen-4.0-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",
        ),
    )

    if not response.generated_images:
        raise ValueError("Gemini에서 이미지를 생성하지 못했습니다")

    image_bytes = response.generated_images[0].image.image_bytes
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"


PROVIDERS = {
    "openai": _generate_with_openai,
    "gemini": _generate_with_gemini,
}


async def generate_emoji_set(
    features: PetFeatures,
    style: str = "2d",
    emoji_count: int = 8,
    provider: str = "openai",
    custom_prompt: str = "",
    accessory: str = "none",
    background: str = "white",
    time_of_day: str = "none",
) -> list[EmojiResult]:
    """Generate a set of emoji images using the selected AI provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"지원하지 않는 provider: {provider}. 가능: {list(PROVIDERS.keys())}")

    generate_fn = PROVIDERS[provider]
    base_prompt = _build_character_prompt(
        features,
        style,
        custom_prompt,
        accessory,
        background,
        time_of_day,
    )

    has_scene_bg = background not in ("white", "transparent", "gradient")

    emotions_to_generate = EMOTIONS[:emoji_count]
    results: list[EmojiResult] = []

    for emotion, description in emotions_to_generate:
        suffix = "No text, no watermark."
        if not has_scene_bg:
            suffix += " Clean background."

        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
{suffix}"""

        logger.info("Generating %s emoji with %s", emotion, provider)
        image_url = await generate_fn(prompt)
        results.append(EmojiResult(emotion=emotion, image_url=image_url))

    return results
