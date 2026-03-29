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


def _build_character_prompt(features: PetFeatures, style: str, custom_prompt: str = "") -> str:
    """Build the base character description from pet features."""
    style_desc = (
        "clean 2D vector art style, flat colors, bold outlines, like Kakao Friends or LINE stickers"
        if style == "2d"
        else "cute 3D rendered style, soft lighting, clay/vinyl figure look, like Pop Mart figurines"
    )

    base = f"""A cute character based on a {features.animal_type} ({features.breed}).
Physical traits: {features.fur_color} {features.fur_pattern} fur, {features.ear_shape} ears, {features.eye_shape} {features.eye_color} eyes, {features.nose_shape} nose, {features.body_shape} body.
Distinctive features: {", ".join(features.distinctive_features)}.
Style: {style_desc}.
The character should be chibi-proportioned (big head, small body), centered on a white background, emoji-sized square composition."""

    if custom_prompt:
        base += f"\nAdditional instructions: {custom_prompt}"

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
) -> list[EmojiResult]:
    """Generate a set of emoji images using the selected AI provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"지원하지 않는 provider: {provider}. 가능: {list(PROVIDERS.keys())}")

    generate_fn = PROVIDERS[provider]
    base_prompt = _build_character_prompt(features, style, custom_prompt)

    emotions_to_generate = EMOTIONS[:emoji_count]
    results: list[EmojiResult] = []

    for emotion, description in emotions_to_generate:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

        logger.info("Generating %s emoji with %s", emotion, provider)
        image_url = await generate_fn(prompt)
        results.append(EmojiResult(emotion=emotion, image_url=image_url))

    return results
