import anthropic
import base64
import json

from app.models.schemas import PetFeatures


async def analyze_pet_photo(image_bytes: bytes, content_type: str) -> PetFeatures:
    """Use Claude Vision to extract pet features from a photo."""
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
                    {
                        "type": "text",
                        "text": """Analyze this pet photo and extract features for creating a character emoji set (like Kakao Friends style).

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

Return ONLY the JSON, no other text.""",
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text
    # Clean up response if wrapped in code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0]

    features_dict = json.loads(response_text)
    return PetFeatures(**features_dict)
