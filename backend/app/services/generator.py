import base64

from openai import OpenAI

from app.models.schemas import EmojiResult, PetFeatures

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


def _build_character_prompt(features: PetFeatures, style: str) -> str:
    """Build the base character description from pet features."""
    style_desc = (
        "clean 2D vector art style, flat colors, bold outlines, like Kakao Friends or LINE stickers"
        if style == "2d"
        else "cute 3D rendered style, soft lighting, clay/vinyl figure look, like Pop Mart figurines"
    )

    return f"""A cute character based on a {features.animal_type} ({features.breed}).
Physical traits: {features.fur_color} {features.fur_pattern} fur, {features.ear_shape} ears, {features.eye_shape} {features.eye_color} eyes, {features.nose_shape} nose, {features.body_shape} body.
Distinctive features: {', '.join(features.distinctive_features)}.
Style: {style_desc}.
The character should be chibi-proportioned (big head, small body), centered on a white background, emoji-sized square composition."""


async def generate_emoji_set(
    features: PetFeatures,
    style: str = "2d",
    emoji_count: int = 8,
) -> list[EmojiResult]:
    """Generate a set of emoji images using GPT-4o image generation."""
    client = OpenAI()
    base_prompt = _build_character_prompt(features, style)

    emotions_to_generate = EMOTIONS[:emoji_count]
    results: list[EmojiResult] = []

    for emotion, description in emotions_to_generate:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="medium",
        )

        image_b64 = response.data[0].b64_json
        if not image_b64:
            # If b64 not available, try URL
            image_url = response.data[0].url or ""
        else:
            image_url = f"data:image/png;base64,{image_b64}"

        results.append(EmojiResult(emotion=emotion, image_url=image_url))

    return results
