"""Runway 기반 움직이는 이모지 생성 서비스.

정지 이모지 이미지를 Runway Gen-4 Turbo image-to-video로 애니메이션화한다.
비용이 발생하는 기능이므로 프리미엄 티어 전용 (클립당 ~$0.25).
"""

import asyncio
import logging
import os

import httpx

logger = logging.getLogger(__name__)

RUNWAY_API_BASE = "https://api.dev.runwayml.com/v1"
RUNWAY_API_VERSION = "2024-11-06"
RUNWAY_MODEL = "gen4_turbo"
RUNWAY_RATIO = "960:960"
RUNWAY_DURATION = 5  # 최소 단위 (초)

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


def is_configured() -> bool:
    """Runway API 키가 설정되어 있는지 확인."""
    return bool(os.getenv("RUNWAY_API_KEY"))


def _build_motion_prompt(emotion: str) -> str:
    lower = emotion.lower()
    for key, prompt in MOTION_PROMPTS.items():
        if key in lower:
            return prompt + STYLE_SUFFIX
    return DEFAULT_MOTION_PROMPT + STYLE_SUFFIX


async def generate_motion_video(image_data_url: str, emotion: str) -> bytes:
    """이모지 이미지를 감정에 맞는 짧은 영상(mp4 bytes)으로 변환.

    Raises:
        RuntimeError: API 키 미설정, 생성 실패, 타임아웃
    """
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        raise RuntimeError("RUNWAY_API_KEY가 설정되지 않았습니다")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Runway-Version": RUNWAY_API_VERSION,
    }
    payload = {
        "model": RUNWAY_MODEL,
        "promptImage": image_data_url,
        "promptText": _build_motion_prompt(emotion),
        "ratio": RUNWAY_RATIO,
        "duration": RUNWAY_DURATION,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{RUNWAY_API_BASE}/image_to_video", json=payload, headers=headers
        )
        response.raise_for_status()
        task_id = response.json()["id"]
        logger.info("Runway task created: %s (emotion=%s)", task_id, emotion)

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
