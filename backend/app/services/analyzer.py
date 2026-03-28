import logging
import re
import base64
import json

from app.models.schemas import PetFeatures

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze this pet photo and extract features for creating a character emoji set (like Kakao Friends style).

Return a JSON object with these exact fields:
{
    "animal_type": "dog/cat/rabbit/etc",
    "breed": "specific breed or mixed",
    "fur_color": "primary fur colors",
    "fur_pattern": "solid/spotted/striped/tuxedo/etc",
    "ear_shape": "floppy/pointy/folded/long/etc",
    "eye_color": "color",
    "eye_shape": "round/almond/big/small",
    "nose_shape": "round/pointed/flat/etc",
    "body_shape": "slim/chubby/muscular/fluffy/etc",
    "distinctive_features": ["list of unique features like spots, curly tail, etc"],
    "current_expression": "happy/sleepy/curious/etc",
    "overall_vibe": "cute/majestic/goofy/elegant/etc"
}

Return ONLY the JSON, no other text."""


def _parse_features(response_text: str) -> PetFeatures:
    """Parse JSON from AI response into PetFeatures."""
    response_text = response_text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]

    json_match = re.search(r"\{[\s\S]*\}", response_text)
    if not json_match:
        logger.error("No JSON found in response: %s", response_text[:200])
        raise ValueError("응답에서 JSON을 찾을 수 없습니다")

    try:
        features_dict = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        logger.error("JSON parse error: %s | Response: %s", e, response_text[:200])
        raise ValueError(f"JSON 파싱 실패: {e}") from e

    try:
        return PetFeatures(**features_dict)
    except Exception as e:
        logger.error("PetFeatures validation error: %s | Data: %s", e, features_dict)
        raise ValueError(f"특징 데이터 검증 실패: {e}") from e


async def _analyze_with_anthropic(image_bytes: bytes, content_type: str) -> PetFeatures:
    """Analyze pet photo using Claude Vision."""
    import anthropic

    client = anthropic.Anthropic()
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": content_type,
                            "data": base64_image,
                        },
                    },
                    {"type": "text", "text": ANALYSIS_PROMPT},
                ],
            }
        ],
    )

    return _parse_features(message.content[0].text)


async def _analyze_with_gemini(image_bytes: bytes, content_type: str) -> PetFeatures:
    """Analyze pet photo using Gemini Vision."""
    from google import genai
    from google.genai import types

    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                parts=[
                    types.Part.from_bytes(data=image_bytes, mime_type=content_type),
                    types.Part.from_text(text=ANALYSIS_PROMPT),
                ]
            )
        ],
    )

    return _parse_features(response.text)


ANALYZERS = {
    "anthropic": _analyze_with_anthropic,
    "gemini": _analyze_with_gemini,
}


async def analyze_pet_photo(
    image_bytes: bytes,
    content_type: str,
    analyzer: str = "gemini",
) -> PetFeatures:
    """Analyze pet photo using the selected AI provider."""
    if analyzer not in ANALYZERS:
        raise ValueError(f"지원하지 않는 analyzer: {analyzer}. 가능: {list(ANALYZERS.keys())}")

    logger.info("Analyzing pet photo with %s", analyzer)
    return await ANALYZERS[analyzer](image_bytes, content_type)
