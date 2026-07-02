"""움직이는 이모지 생성 서비스 (image-to-video).

정지 이모지 이미지를 AI 영상 모델로 애니메이션화한다.
비용이 발생하는 기능이므로 프리미엄 티어 전용.

프로바이더:
- veo: Gemini API의 Veo 3.1 Fast (기존 GOOGLE_API_KEY 재사용, 4초 ~$0.60)
- runway: Runway Gen-4 Turbo (RUNWAY_API_KEY 필요, 5초 ~$0.25)

VIDEO_PROVIDER 환경변수로 강제 지정 가능. 미지정 시 runway → veo 순으로 자동 선택.
"""

import asyncio
import base64
import logging
import os

import httpx

logger = logging.getLogger(__name__)

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_API_VERSION = "2024-11-06"
RUNWAY_MODEL = "gen4_turbo"
RUNWAY_RATIO = "960:960"
RUNWAY_DURATION = 5  # 최소 단위 (초)

VEO_MODEL = "veo-3.1-fast-generate-preview"
VEO_DURATION = 4  # 지원 옵션 중 최소 (초)

POLL_INTERVAL_SECONDS = 5
MAX_POLL_ATTEMPTS = 60  # 최대 5분 대기

# 감정별 모션 프롬프트 (움직임 묘사만, 캐릭터 외형은 입력 이미지가 결정)
MOTION_PROMPTS: dict[str, str] = {
    "happy": "The character bounces up and down joyfully, tail wagging fast",
    "sad": "The character's ears and shoulders droop slowly, sighing gently",
    "angry": "The character trembles with puffed cheeks, stomping in place",
    "sleepy": "The character sways drowsily, eyes slowly blinking closed",
    "love": "The character sways side to side happily, tail wagging softly",
    "surprised": "The character jumps back startled, then blinks wide-eyed",
    "cool": "The character sways confidently side to side with a smirk",
    "celebrate": "The character hops excitedly, confetti floating around",
    "eating": "The character munches happily, cheeks puffing with each bite",
    "crying": "The character sobs, shoulders shaking, tears rolling down",
    "greeting": "The character waves one paw in a friendly greeting",
    "running": "The character runs in place energetically, legs moving fast",
}
DEFAULT_MOTION_PROMPT = "The character moves gently in place with a subtle idle animation"

STYLE_SUFFIX = (
    " Subtle looping motion, the character stays centered in place, "
    "static plain white background, no camera movement, no zoom, cute sticker style."
)


def get_provider() -> str | None:
    """사용할 영상 프로바이더 결정. 사용 불가 시 None."""
    forced = os.getenv("VIDEO_PROVIDER")
    if forced in ("runway", "veo"):
        return forced
    if os.getenv("RUNWAY_API_KEY"):
        return "runway"
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return "veo"
    return None


def is_configured() -> bool:
    """영상 생성 프로바이더가 설정되어 있는지 확인."""
    return get_provider() is not None


def _build_motion_prompt(emotion: str) -> str:
    lower = emotion.lower()
    for key, prompt in MOTION_PROMPTS.items():
        if key in lower:
            return prompt + STYLE_SUFFIX
    return DEFAULT_MOTION_PROMPT + STYLE_SUFFIX


def _decode_data_url(image_data_url: str) -> tuple[bytes, str]:
    """data URL에서 (bytes, mime_type) 추출."""
    header, b64_data = image_data_url.split(",", 1)
    mime_type = header.split(":", 1)[1].split(";", 1)[0]
    return base64.b64decode(b64_data), mime_type


async def _generate_with_runway(image_data_url: str, prompt: str) -> bytes:
    """Runway Gen-4 Turbo로 영상 생성."""
    api_key = os.environ["RUNWAY_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }
    payload = {
        "model": RUNWAY_MODEL,
        "promptImage": image_data_url,
        "promptText": prompt,
        "ratio": RUNWAY_RATIO,
        "duration": RUNWAY_DURATION,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{RUNWAY_API_BASE}/image_to_video", json=payload, headers=headers
        )
        if response.status_code == 400 and "credits" in response.text.lower():
            logger.error("Runway credits exhausted")
            raise RuntimeError("Runway API 크레딧이 부족합니다")
        response.raise_for_status()
        task_id = response.json()["id"]
        logger.info("Runway task created: %s", task_id)

        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            task_response = await client.get(f"{RUNWAY_API_BASE}/tasks/{task_id}", headers=headers)
            task_response.raise_for_status()
            task = task_response.json()
            status = task.get("status")

            if status == "SUCCEEDED":
                video_url = task["output"][0]
                video_response = await client.get(video_url)
                video_response.raise_for_status()
                logger.info(
                    "Runway task %s succeeded (%d bytes)", task_id, len(video_response.content)
                )
                return video_response.content

            if status == "FAILED":
                logger.error("Runway task %s failed: %s", task_id, task.get("failure"))
                raise RuntimeError("영상 생성에 실패했습니다")

    raise RuntimeError("영상 생성 시간이 초과되었습니다")


async def _generate_with_veo(image_data_url: str, prompt: str) -> bytes:
    """Gemini API의 Veo 3.1 Fast로 영상 생성."""
    from google import genai
    from google.genai import types

    image_bytes, mime_type = _decode_data_url(image_data_url)
    client = genai.Client()

    operation = await client.aio.models.generate_videos(
        model=VEO_MODEL,
        prompt=prompt,
        image=types.Image(image_bytes=image_bytes, mime_type=mime_type),
        config=types.GenerateVideosConfig(duration_seconds=VEO_DURATION),
    )
    logger.info("Veo operation created: %s", operation.name)

    for _ in range(MAX_POLL_ATTEMPTS):
        if operation.done:
            break
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        operation = await client.aio.operations.get(operation)
    else:
        raise RuntimeError("영상 생성 시간이 초과되었습니다")

    if operation.error:
        logger.error("Veo operation failed: %s", operation.error)
        raise RuntimeError("영상 생성에 실패했습니다")

    video = operation.response.generated_videos[0]
    # async 클라이언트는 bytes를 반환, sync는 video_bytes 필드에 채움 — 둘 다 대응
    downloaded = await client.aio.files.download(file=video.video)
    video_bytes = downloaded if isinstance(downloaded, bytes) else video.video.video_bytes
    if not video_bytes:
        raise RuntimeError("영상 다운로드에 실패했습니다")
    logger.info("Veo video downloaded (%d bytes)", len(video_bytes))
    return video_bytes


_PROVIDERS = {
    "runway": _generate_with_runway,
    "veo": _generate_with_veo,
}


async def generate_motion_video(image_data_url: str, emotion: str) -> bytes:
    """이모지 이미지를 감정에 맞는 짧은 영상(mp4 bytes)으로 변환.

    Raises:
        RuntimeError: 프로바이더 미설정, 생성 실패, 타임아웃
    """
    provider = get_provider()
    if provider is None:
        raise RuntimeError("영상 생성 프로바이더가 설정되지 않았습니다")

    prompt = _build_motion_prompt(emotion)
    logger.info("Generating motion video via %s (emotion=%s)", provider, emotion)
    return await _PROVIDERS[provider](image_data_url, prompt)
