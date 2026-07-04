import asyncio
import base64
import logging

from app.models.schemas import EmojiResult, PetFeatures
from app.services.caption import generate_captions

logger = logging.getLogger(__name__)

# AI API 동시 요청 제한 (rate limit 보호)
MAX_CONCURRENT_GENERATIONS = 5
generation_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GENERATIONS)

# 감정 32종 — 프론트 EmojiGrid.tsx의 EMOTION_LABELS와 키가 1:1로 일치해야 함
EMOTIONS = [
    # 기본 8종
    ("happy", "smiling big with sparkly eyes, tail wagging"),
    ("sad", "teary eyes, droopy ears, looking down"),
    ("angry", "puffed cheeks, furrowed brows, tiny flames"),
    ("sleepy", "half-closed eyes, yawning, zzz floating"),
    ("love", "heart eyes, blushing cheeks, hearts floating around"),
    ("surprised", "wide open eyes and mouth, exclamation mark"),
    ("cool", "wearing tiny sunglasses, confident smirk"),
    ("celebrate", "party hat, confetti, jumping with joy"),
    # 확장 24종 (카카오 이모티콘 기준)
    ("thumbsup", "giving a thumbs up with a big grin, winking"),
    ("thumbsdown", "thumbs down with a disappointed frown, shaking head"),
    ("grateful", "bowing politely with hands together, thankful expression"),
    ("sorry", "hands clasped apologetically, sweating nervously, bowing"),
    ("fighting", "fist pump in the air, determined fierce eyes, fire aura"),
    ("tired", "slouching exhausted, dark circles under eyes, wilting"),
    ("hungry", "drooling with wide eyes, rubbing belly, fork and knife"),
    ("eating", "happily munching food, cheeks full, crumbs flying"),
    ("laughing", "rolling on floor laughing, tears of joy, holding belly"),
    ("crying", "bawling with rivers of tears, mouth wide open sobbing"),
    ("shy", "covering face with paws, blushing bright red, peeking"),
    ("nervous", "trembling with sweat drops, biting lip, shaking"),
    ("bored", "chin resting on hand, half-lidded eyes, yawning slightly"),
    ("excited", "jumping up and down, sparkling eyes, arms raised"),
    ("confused", "question marks floating, tilted head, spiral eyes"),
    ("sick", "green face, thermometer in mouth, ice pack on head"),
    ("hot", "fanning self, sweat drops flying, tongue out panting"),
    ("cold", "shivering wrapped in blanket, blue lips, snowflakes"),
    ("working", "typing on laptop intensely, focused eyes, coffee nearby"),
    ("sleeping", "curled up sleeping peacefully, zzz bubbles, snoring"),
    ("greeting", "waving hand enthusiastically, big smile, saying hi"),
    ("bye", "waving goodbye with teary eyes, blowing a kiss"),
    ("running", "running away frantically, dust cloud behind, scared"),
    ("hugging", "arms wide open for a hug, warm smile, hearts floating"),
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


def sanitize_custom_prompt(prompt: str) -> str:
    """커스텀 프롬프트에서 위험한 패턴 제거."""
    lower = prompt.lower()
    for blocked in PROMPT_BLOCKLIST:
        if blocked in lower:
            return ""
    return prompt


# 스타일 설명 정본 — 무료 플로우와 위자드(graph/prompts.py)가 공유
STYLE_DESCRIPTIONS = {
    "2d": "clean 2D vector art style, flat colors, bold outlines, like Kakao Friends or LINE stickers",
    "3d": "cute 3D rendered style, soft lighting, clay/vinyl figure look, like Pop Mart figurines",
    "watercolor": "soft watercolor painting style, gentle brush strokes, pastel colors, dreamy atmosphere",
    "pixel": "pixel art style, 32x32 retro game character, limited color palette, crisp edges",
    "realistic": "photorealistic digital painting, real fur texture, natural proportions, studio lighting",
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

# 장면(풍경)이 아닌 단색·추상 배경 — 이 목록만 'Clean background' 지시를 받는다.
# BACKGROUND_DESCRIPTIONS에 단색 배경을 추가하면 여기에도 반드시 추가할 것.
PLAIN_BACKGROUNDS = ("white", "transparent", "gradient")

# 장면이 없는 단색/패턴 배경 (이 목록에 없으면 장면 배경으로 취급)
PLAIN_BACKGROUNDS = ("white", "transparent", "gradient")

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


def build_character_prompt(
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

    sanitized = sanitize_custom_prompt(custom_prompt)
    if sanitized:
        base += f"\nAdditional instructions: {sanitized}"

    return base


async def _generate_with_openai(prompt: str) -> str:
    """Generate image using GPT-4o (OpenAI)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    response = await client.images.generate(
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


async def enhance_prompt_with_hermes(prompt: str) -> str:
    """Hermes 로컬 모델로 이미지 프롬프트 최적화."""
    import httpx

    system = """You are an expert image prompt engineer.
Rewrite the given prompt to be more vivid and effective for AI image generation.
Keep the same subject, style, and composition. Enhance descriptive details.
Reply with ONLY the improved prompt, nothing else."""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "nous-hermes2",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.7},
                },
            )
            response.raise_for_status()
            enhanced = response.json()["message"]["content"].strip()
            logger.info("Prompt enhanced by Hermes (%d → %d chars)", len(prompt), len(enhanced))
            return enhanced
    except Exception:
        logger.warning("Hermes prompt enhancement failed, using original")
        return prompt


PROVIDERS = {
    "openai": _generate_with_openai,
    "gemini": _generate_with_gemini,
}


def build_prompt_suffix(background: str = "white") -> str:
    """생성 프롬프트 공통 접미사.

    장면 배경(공원, 카페 등)을 요청한 경우 'Clean background' 지시를 생략해
    배경 설정과 모순되지 않게 한다.
    """
    suffix = "No text, no watermark."
    if background in PLAIN_BACKGROUNDS:
        suffix += " Clean background."
    return suffix


async def generate_emoji_set(
    features: PetFeatures,
    style: str = "2d",
    emoji_count: int = 8,
    provider: str = "openai",
    custom_prompt: str = "",
    accessory: str = "none",
    background: str = "white",
    time_of_day: str = "none",
    add_captions: bool = True,
    enhance_with_hermes: bool = False,
) -> list[EmojiResult]:
    """Generate a set of emoji images using the selected AI provider."""
    if provider not in PROVIDERS:
        raise ValueError(f"지원하지 않는 provider: {provider}. 가능: {list(PROVIDERS.keys())}")

    generate_fn = PROVIDERS[provider]
    base_prompt = build_character_prompt(
        features,
        style,
        custom_prompt,
        accessory,
        background,
        time_of_day,
    )

    suffix = build_prompt_suffix(background)

    emotions_to_generate = EMOTIONS[:emoji_count]

    # 캡션 일괄 생성
    captions: dict[str, str] = {}
    if add_captions:
        captions = await generate_captions(emotions_to_generate, features, provider)

    async def _generate_one(emotion: str, description: str) -> EmojiResult:
        prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
{suffix}"""

        if enhance_with_hermes:
            prompt = await enhance_prompt_with_hermes(prompt)

        logger.info("Generating %s emoji with %s", emotion, provider)
        async with generation_semaphore:
            image_url = await generate_fn(prompt)

        return EmojiResult(
            emotion=emotion,
            image_url=image_url,
            caption=captions.get(emotion, ""),
        )

    results = await asyncio.gather(
        *[_generate_one(emotion, desc) for emotion, desc in emotions_to_generate]
    )

    return list(results)
