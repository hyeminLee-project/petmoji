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

# LLM이 만든 캡션 허용 길이 (벗어나면 fallback 사용, 오버레이는 2줄까지 렌더)
MIN_CAPTION_LENGTH = 4
MAX_CAPTION_LENGTH = 14

# 캡션 허용 문자: 한글 음절, 관용 낱자(ㅋㅎㅠㅜㅡ), 숫자, 영문(zzZ 등), 공백, 허용 특수문자.
# 한자·가나·이모지·깨진 자모(ㅏ, ㄴ 단독 등)는 여기서 걸러진다.
_CAPTION_ALLOWED = re.compile(r"^[가-힣ㅋㅎㅠㅜㅡ0-9a-zA-Z ♥!?~.,…]+$")


def validate_caption(caption: str) -> bool:
    """캡션이 오타·렌더 위험 없이 사용 가능한지 규칙 검증.

    맞춤법 판단이 아니라 기계적 결함(허용 외 문자, 길이 이탈,
    실질 내용 없음)을 걸러내는 1차 방어선이다.
    """
    if not MIN_CAPTION_LENGTH <= len(caption) <= MAX_CAPTION_LENGTH:
        return False
    if not _CAPTION_ALLOWED.match(caption):
        return False
    # 실질 한글 내용 보장 ("ㅋㅋㅋㅋ", "zzZ!!" 같은 낱자·영문 단독 차단)
    hangul_count = sum(1 for ch in caption if "가" <= ch <= "힣")
    return hangul_count >= 2


# LLM 호출 실패 시 기본 캡션 (감정별 2개씩, 랜덤 선택)
# 단순 감탄사가 아니라 카톡에서 실제로 보낼 법한 상황 대사로 유지할 것
CAPTION_FALLBACKS: dict[str, list[str]] = {
    "happy": ["오늘 최고의 날!", "기분 째진다~!"],
    "sad": ["나 좀 안아줘...", "오늘은 슬픈 날.."],
    "angry": ["나 진짜 화났어!!", "건들지 마라..."],
    "sleepy": ["5분만 더 잘래..", "눈이 감긴다..zzZ"],
    "love": ["너밖에 없어♥", "심장 터질 것 같아"],
    "surprised": ["뭐?! 진짜야?!", "이게 무슨 일이야!"],
    "cool": ["이 구역 짱은 나야", "부럽지? 후훗"],
    "celebrate": ["우리 해냈어!!", "오늘은 파티다~!"],
    "thumbsup": ["인정! 완전 최고", "그거 완전 좋은데?"],
    "thumbsdown": ["음.. 그건 좀 별로", "다시 생각해봐..."],
    "grateful": ["진짜 고마워요♥", "은혜 잊지 않을게!"],
    "sorry": ["내가 잘못했어...", "한 번만 봐줘요.."],
    "fighting": ["오늘도 파이팅!!", "할 수 있어, 가자!"],
    "tired": ["기절 직전이야...", "체력 바닥났어.."],
    "hungry": ["밥 주세요 제발..", "배에서 천둥소리가"],
    "eating": ["먹을 때가 젤 행복해", "이 맛에 산다니까~"],
    "laughing": ["아 배 아파 ㅋㅋㅋ", "숨 넘어가겠다 ㅋㅋ"],
    "crying": ["나 오늘 울 거야..", "눈물이 안 멈춰 ㅠㅠ"],
    "shy": ["보지 마.. 부끄러워", "아 왜 그래~ 부끄럽게"],
    "nervous": ["심장이 벌렁벌렁해", "떨려서 미치겠어.."],
    "bored": ["심심해 죽겠어~", "나랑 놀아줘라..."],
    "excited": ["미쳤다 미쳤어!!", "완전 신나는데?!"],
    "confused": ["뭐라는 거야 지금?", "내가 뭘 본 거지..?"],
    "sick": ["나 아픈 것 같아..", "병원 가기 싫어.."],
    "hot": ["녹아내리는 중...", "에어컨 어딨어!!"],
    "cold": ["얼어 죽겠어 덜덜", "이불 밖은 위험해"],
    "working": ["일하는 중 방해금지", "마감이 코앞이야.."],
    "sleeping": ["먼저 잘게 굿나잇~", "꿈에서 만나자..zzZ"],
    "greeting": ["왔어? 반가워~!", "안녕! 보고싶었어"],
    "bye": ["잘 가, 또 보자~!", "벌써 가? 아쉽다.."],
    "running": ["나 먼저 도망간다!!", "튀어!! 잡히면 끝장"],
    "hugging": ["이리 와, 안아줄게", "꼬옥 안아줘 지금"],
}

CAPTION_SYSTEM_PROMPT = """너는 귀여운 {animal_type}({breed}) 캐릭터야.
성격: {vibe}

카카오톡에서 이 이모티콘을 보내는 사람이 "대신 하고 싶은 말"을 만들어줘.
감정 이름을 설명하는 게 아니라, 실제 대화에서 보낼 법한 생동감 있는 한마디여야 해.

규칙:
- 4~12자 (짧은 문장 하나, 두 줄까지 표시 가능)
- 상황이 그려지는 구체적인 대사 ("흑흑...", "신난다!" 같은 단편적 감탄사 금지)
- 이 캐릭터가 직접 말하는 것처럼, 성격에 맞는 말투로 통일 (반말/존댓말/도도/애교 중 하나)
- 감정마다 문장 형태를 다르게 (감탄, 질문, 명령, 선언, 부탁을 섞기)
- 특수문자는 양념으로만 (♥, !, ?, ~, ... ㅋㅋ ㅠㅠ)
- 같은 표현 반복 금지 (모든 대사가 서로 달라야 함)
- 반드시 JSON 형식으로 반환

예시 (도도한 고양이):
{{"happy": "오늘 좀 괜찮네", "sad": "나 삐졌어. 진심", "angry": "지금 나 건드렸어?", "hungry": "밥. 지금. 당장", "love": "...너니까 봐주는 거야", "surprised": "뭐? 다시 말해봐", "sleepy": "낮잠 방해하면 끝이야"}}

예시 (활발한 강아지):
{{"happy": "오늘 최고의 날!!", "sad": "나 좀 안아줘...", "angry": "나 진짜 화났어!!", "hungry": "밥 주세요 제발!!", "love": "너밖에 없어 진짜♥", "surprised": "뭐?! 진짜야?!", "sleepy": "5분만 더 잘래.."}}

예시 (새침한 토끼):
{{"happy": "기분 좋아졌어 후후", "sad": "오늘은 말 걸지 마", "angry": "나 화난 거 안 보여?", "hungry": "당근 사와. 두 개", "love": "좋아하는 거 아니거든?", "surprised": "심장 떨어질 뻔했잖아", "sleepy": "먼저 잘게. 굿나잇"}}"""

CAPTION_USER_PROMPT = """다음 감정 목록에 대한 캐릭터 대사를 만들어줘:

{emotions}

각 항목을 emotion(감정 키)과 caption(대사) 필드로 반환해."""

# 셀프 교정: 맞춤법 실수만 고치고 의도적 구어체는 보존, 감정 불일치는 REJECT
PROOFREAD_REJECT = "REJECT"

PROOFREAD_SYSTEM_PROMPT = """너는 한국어 이모티콘 대사 검수 전문가야.
주어진 감정별 대사에서 진짜 맞춤법 실수만 고쳐줘.

규칙:
- 명백한 실수만 교정 (예: 됬어→됐어, 안되→안돼, 어의없어→어이없어, 잘못된 띄어쓰기)
- 의도적 구어체·신조어·말줄임은 절대 건드리지 마 ("째진다", "젤", "넘", "~라니까", "꼬옥" 등)
- 특수문자(♥ ! ? ~ ... ㅋㅋ ㅠㅠ)와 말투는 그대로 유지
- 대사가 해당 감정과 명백히 안 맞으면 caption을 "REJECT"로만 표시
- 고칠 것이 없으면 원문 그대로 반환
- 모든 항목을 emotion과 caption 필드로 반환"""

PROOFREAD_USER_PROMPT = """다음 감정별 대사를 검수해줘:

{items}"""

# 구조화 출력 스키마 — 파싱 실패와 깨진 JSON을 원천 차단
# (Gemini는 배열을 직접, OpenAI strict 모드는 {"captions": [...]}로 감싸서 반환)
CAPTION_ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "emotion": {"type": "STRING"},
        "caption": {"type": "STRING"},
    },
    "required": ["emotion", "caption"],
}
GEMINI_RESPONSE_SCHEMA = {"type": "ARRAY", "items": CAPTION_ITEM_SCHEMA}
OPENAI_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "captions",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "captions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "emotion": {"type": "string"},
                            "caption": {"type": "string"},
                        },
                        "required": ["emotion", "caption"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["captions"],
            "additionalProperties": False,
        },
    },
}


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
    """비구조화 응답(hermes 전용)에서 JSON 캡션 딕셔너리 파싱."""
    text = response_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]

    json_match = re.search(r"\{[\s\S]*\}", text)
    if not json_match:
        raise ValueError("응답에서 JSON을 찾을 수 없습니다")

    return json.loads(json_match.group())


def _parse_caption_items(raw: str) -> dict[str, str]:
    """구조화 출력을 {emotion: caption} 딕셔너리로 변환.

    Gemini는 배열([{emotion, caption}, ...])을, OpenAI strict 모드는
    {"captions": [...]} 형태를 반환하므로 둘 다 처리한다.
    """
    data = json.loads(raw)
    if isinstance(data, dict):
        data = data.get("captions", [])
    return {item["emotion"]: item["caption"] for item in data if item.get("emotion")}


async def _generate_with_openai(system: str, user: str, temperature: float = 0.8) -> str:
    """OpenAI로 캡션 생성/교정 (구조화 출력)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=2048,
        response_format=OPENAI_RESPONSE_FORMAT,
    )
    return response.choices[0].message.content or ""


async def _generate_with_gemini(system: str, user: str, temperature: float = 0.8) -> str:
    """Gemini로 캡션 생성/교정 (구조화 출력)."""
    from google import genai
    from google.genai import types

    client = genai.Client()
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=2048,
            response_mime_type="application/json",
            response_schema=GEMINI_RESPONSE_SCHEMA,
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


async def _proofread_captions(captions: dict[str, str], provider: str) -> dict[str, str]:
    """LLM 셀프 교정: 맞춤법 실수만 수정하고 감정 불일치 대사는 비운다.

    교정은 부가 단계라 호출이 실패하면 원본을 그대로 반환한다.
    REJECT 판정은 빈 문자열이 되어 상위에서 fallback으로 대체된다.
    hermes는 구조화 출력 미지원이라 건너뛴다.
    """
    if not captions or provider == "hermes":
        return captions

    items = json.dumps(
        [{"emotion": e, "caption": c} for e, c in captions.items()], ensure_ascii=False
    )
    user = PROOFREAD_USER_PROMPT.format(items=items)

    try:
        if provider == "openai":
            raw = await _generate_with_openai(PROOFREAD_SYSTEM_PROMPT, user, temperature=0.1)
        else:
            raw = await _generate_with_gemini(PROOFREAD_SYSTEM_PROMPT, user, temperature=0.1)
        corrected = _parse_caption_items(raw)
    except Exception:
        logger.warning("Caption proofread failed, keeping originals")
        return captions

    result = {}
    for emotion, original in captions.items():
        fixed = corrected.get(emotion, original)
        if fixed == PROOFREAD_REJECT:
            logger.info("Caption rejected by proofread for %s: %r", emotion, original)
            fixed = ""
        elif fixed != original:
            logger.info("Caption corrected for %s: %r -> %r", emotion, original, fixed)
        result[emotion] = fixed
    return result


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
            captions = _parse_caption_items(raw)
        elif provider == "hermes":
            # 로컬 모델은 구조화 출력 미지원 — 기존 정규식 파싱 유지
            raw = await _generate_with_hermes(system, user)
            captions = _parse_captions(raw)
        else:
            raw = await _generate_with_gemini(system, user)
            captions = _parse_caption_items(raw)

        logger.info("Generated %d captions via %s", len(captions), provider)

    except Exception:
        logger.exception("Caption generation failed, using fallbacks")
        captions = {}

    # 셀프 교정: 맞춤법 수정 + 감정 불일치 REJECT (실패 시 원본 유지)
    captions = await _proofread_captions(captions, provider)

    # 누락되거나 검증(문자·길이·내용)을 통과하지 못한 감정은 fallback에서 랜덤 선택
    result = {}
    for emotion, _ in emotions:
        generated = captions.get(emotion, "")
        if generated and validate_caption(generated):
            result[emotion] = generated
        else:
            if generated:
                logger.info("Caption rejected for %s: %r, using fallback", emotion, generated)
            fallbacks = CAPTION_FALLBACKS.get(emotion, [""])
            result[emotion] = random.choice(fallbacks)

    return result
