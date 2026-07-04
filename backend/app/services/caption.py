"""감정별 한국어 캡션 생성 서비스.

LLM 1회 호출로 모든 감정에 대한 캐릭터 대사를 일괄 생성한다.
펫의 성격(overall_vibe)과 동물 종류를 반영하여 개성 있는 대사를 만든다.
"""

import json
import logging
import random
import re

from app.models.schemas import PetFeatures

logger = logging.getLogger(__name__)

# LLM 호출 실패 시 기본 캡션 (감정별 2개씩, 랜덤 선택)
CAPTION_FALLBACKS: dict[str, list[str]] = {
    "happy": ["좋아좋아!", "헤헤~♥"],
    "sad": ["흑흑...", "서러워..."],
    "angry": ["화나!!!", "으르르!"],
    "sleepy": ["졸려..zzZ", "꾸벅.."],
    "love": ["좋아해♥", "두근두근!"],
    "surprised": ["헉!?", "깜짝이야!"],
    "cool": ["멋지지?", "후훗~"],
    "celebrate": ["파티다!", "축하해~!"],
    "thumbsup": ["최고!", "굿굿~!"],
    "thumbsdown": ["별로야...", "에잇..."],
    "grateful": ["고마워~", "감사해요!"],
    "sorry": ["미안해...", "죄송..."],
    "fighting": ["파이팅!", "할수있다!"],
    "tired": ["지쳤어...", "녹초..."],
    "hungry": ["밥 줘...", "배고파~"],
    "eating": ["냠냠!", "맛있다~!"],
    "laughing": ["ㅋㅋㅋㅋ", "빵!ㅋㅋ"],
    "crying": ["흑흑흑...", "으앙..."],
    "shy": ["부끄러...", "어머...//"],
    "nervous": ["떨려...", "두근두근.."],
    "bored": ["심심해~", "하아암~"],
    "excited": ["신난다!", "우와아!"],
    "confused": ["뭐지?", "응??"],
    "sick": ["아파...", "으으..."],
    "hot": ["더워~!", "헥헥..."],
    "cold": ["추워...", "덜덜..."],
    "working": ["집중!", "열공!"],
    "sleeping": ["쿨쿨..zzZ", "드르렁~"],
    "greeting": ["안녕!", "반가워~!"],
    "bye": ["잘 가~", "또 봐~!"],
    "running": ["도망가!", "살려줘~!"],
    "hugging": ["안아줘~", "꼬옥♥"],
}

CAPTION_SYSTEM_PROMPT = """너는 귀여운 {animal_type}({breed}) 캐릭터야.
성격: {vibe}

각 감정에 어울리는 짧은 한국어 대사를 만들어줘.
이 캐릭터가 직접 말하는 것처럼, 성격이 자연스럽게 드러나야 해.

규칙:
- 2~8자 이내 (말풍선에 들어갈 크기)
- 말투는 캐릭터 성격에 맞게 통일 (반말/존댓말/도도/애교 등 하나로)
- 감탄사, 의성어, 의태어 적극 활용 ("으르르!", "냠냠~", "두근두근")
- 특수문자 자연스럽게 섞기 (♥, !, ?, ~, ... ㅋㅋ ㅠㅠ 등)
- 같은 표현 반복하지 말 것 (모든 대사가 다르게)
- 반드시 JSON 형식으로 반환

예시 (도도한 고양이):
{{"happy": "...나쁘지않아", "sad": "흥...", "angry": "건드리지마", "hungry": "밥.", "love": "...좋아해", "surprised": "뭐야!?", "sleepy": "방해하지마.."}}

예시 (활발한 강아지):
{{"happy": "좋아좋아!", "sad": "흑흑..ㅠ", "angry": "으르르!", "hungry": "밥밥밥!", "love": "사랑해!!", "surprised": "깜짝이야!", "sleepy": "자고싶다~"}}

예시 (새침한 토끼):
{{"happy": "후후~", "sad": "삐짐...", "angry": "어이없어", "hungry": "당근줘~", "love": "몰라몰라//", "surprised": "엇!?", "sleepy": "자는중..zzZ"}}"""

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
        model="gemini-2.5-flash",
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.8,
            max_output_tokens=1024,
        ),
    )
    return response.text or ""


async def _generate_with_hermes(system: str, user: str) -> str:
    """Hermes (Ollama) 로컬 모델로 캡션 생성."""
    import httpx

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "nous-hermes2",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {"temperature": 0.8},
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


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
        elif provider == "hermes":
            raw = await _generate_with_hermes(system, user)
        else:
            raw = await _generate_with_gemini(system, user)

        captions = _parse_captions(raw)
        logger.info("Generated %d captions via %s", len(captions), provider)

    except Exception:
        logger.exception("Caption generation failed, using fallbacks")
        captions = {}

    # 누락된 감정은 fallback에서 랜덤 선택
    result = {}
    for emotion, _ in emotions:
        if emotion in captions and captions[emotion]:
            result[emotion] = captions[emotion]
        else:
            fallbacks = CAPTION_FALLBACKS.get(emotion, [""])
            result[emotion] = random.choice(fallbacks)

    return result
