"""감정별 한국어 캡션 생성 서비스.

LLM 1회 호출로 모든 감정에 대한 캐릭터 대사를 일괄 생성한다.
펫의 성격(overall_vibe)과 동물 종류를 반영하여 개성 있는 대사를 만든다.
"""

import json
import logging
import re

from app.models.schemas import PetFeatures

logger = logging.getLogger(__name__)

# LLM 호출 실패 시 기본 캡션
CAPTION_FALLBACKS: dict[str, str] = {
    "happy": "좋아좋아!",
    "sad": "흑흑...",
    "angry": "화나!",
    "sleepy": "졸려..zzZ",
    "love": "좋아해♥",
    "surprised": "헉!?",
    "cool": "멋지지?",
    "celebrate": "파티다!",
    "thumbsup": "최고!",
    "thumbsdown": "별로야...",
    "grateful": "고마워~",
    "sorry": "미안해...",
    "fighting": "파이팅!",
    "tired": "지쳤어...",
    "hungry": "밥 줘...",
    "eating": "냠냠!",
    "laughing": "ㅋㅋㅋㅋ",
    "crying": "흑흑흑...",
    "shy": "부끄러...",
    "nervous": "떨려...",
    "bored": "심심해~",
    "excited": "신난다!",
    "confused": "뭐지?",
    "sick": "아파...",
    "hot": "더워~!",
    "cold": "추워...",
    "working": "집중!",
    "sleeping": "쿨쿨..zzZ",
    "greeting": "안녕!",
    "bye": "잘 가~",
    "running": "도망가!",
    "hugging": "안아줘~",
}

CAPTION_SYSTEM_PROMPT = """너는 귀여운 {animal_type}({breed}) 캐릭터야.
성격: {vibe}

각 감정에 어울리는 짧은 한국어 대사를 만들어줘.
이 캐릭터가 직접 말하는 것처럼, 성격이 드러나게 써줘.

규칙:
- 1~6자 이내의 짧은 대사 (이모지 위에 올라가야 해서 짧아야 함)
- 말투는 캐릭터 성격에 맞게 (예: 도도한 고양이 → "...뭐", 활발한 강아지 → "좋아좋아!")
- 이모티콘/특수문자 사용 가능 (♥, !, ?, ~, ... 등)
- 반드시 JSON 형식으로 반환

예시 (도도한 고양이):
{{"happy": "...좋아", "sad": "흥...", "angry": "건드리지마", "hungry": "밥.", "love": "...좋아해"}}

예시 (활발한 강아지):
{{"happy": "좋아좋아!", "sad": "흑흑...", "angry": "멍멍!", "hungry": "밥밥밥!", "love": "사랑해!!"}}"""

CAPTION_USER_PROMPT = """다음 감정 목록에 대한 캐릭터 대사를 JSON으로 만들어줘:

{emotions}

JSON만 반환해. 다른 텍스트 없이."""


def _build_caption_prompt(
    features: PetFeatures, emotions: list[tuple[str, str]]
) -> tuple[str, str]:
    """캡션 생성용 시스템/유저 프롬프트 생성."""
    system = CAPTION_SYSTEM_PROMPT.format(
        animal_type=features.animal_type,
        breed=features.breed,
        vibe=features.overall_vibe,
    )
    emotion_list = ", ".join(f'"{e}"' for e, _ in emotions)
    user = CAPTION_USER_PROMPT.format(emotions=emotion_list)
    return system, user


def _parse_captions(response_text: str) -> dict[str, str]:
    """LLM 응답에서 JSON 캡션 딕셔너리 파싱."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("응답에서 JSON을 찾을 수 없습니다")

    return json.loads(json_match.group())


async def _generate_with_openai(system: str, user: str) -> str:
    """OpenAI로 캡션 생성."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.8,
        max_tokens=1024,
    )
    return response.choices[0].message.content or ""


async def _generate_with_gemini(system: str, user: str) -> str:
    """Gemini로 캡션 생성."""
    from google import genai
    from google.genai import types

    client = genai.Client()
    response = await client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.8,
            max_output_tokens=1024,
        ),
    )
    return response.text or ""


async def generate_captions(
    emotions: list[tuple[str, str]],
    features: PetFeatures,
    provider: str = "gemini",
) -> dict[str, str]:
    """감정 목록에 대한 한국어 캡션을 일괄 생성.

    Args:
        emotions: (emotion_key, description) 튜플 리스트
        features: 펫 특징 정보
        provider: LLM 프로바이더 ("openai" 또는 "gemini")

    Returns:
        {emotion_key: caption_text} 딕셔너리
    """
    system, user = _build_caption_prompt(features, emotions)

    try:
        if provider == "openai":
            raw = await _generate_with_openai(system, user)
        else:
            raw = await _generate_with_gemini(system, user)

        captions = _parse_captions(raw)
        logger.info("Generated %d captions via %s", len(captions), provider)

    except Exception:
        logger.exception("Caption generation failed, using fallbacks")
        captions = {}

    # 누락된 감정은 fallback으로 채우기
    result = {}
    for emotion, _ in emotions:
        result[emotion] = captions.get(emotion, CAPTION_FALLBACKS.get(emotion, ""))

    return result
