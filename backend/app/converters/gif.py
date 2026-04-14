"""움직이는 이모지 GIF 변환기.

감정별 자연스러운 모션을 적용하여 GIF 애니메이션 생성.
- happy: 신나게 통통 튀기 + 꼬리 흔드는 듯한 좌우 흔들림
- sad: 축 처지며 느리게 고개 숙임
- angry: 빠르게 부들부들 떨림
- sleepy: 느린 호흡 (천천히 오르내림)
- love: 두근두근 심장 박동 (확대-축소 반복)
- surprised: 깜짝 놀라 위로 점프 + 착지 스쿼시
- cool: 여유롭게 좌우로 스웨이
- celebrate: 점프하며 좌우 회전

카카오 움직이는 이모티콘 규격:
- 360x360px, 72dpi, ≤650KB/개, 총 24개 (PNG 21 + GIF 3)
"""

import math
from dataclasses import dataclass

from PIL import Image

from app.converters.base import decode_image, encode_gif
from app.converters.kakao import KAKAO_COUNT_LIMITS
from app.converters.kakao import SIZE_LIMITS as KAKAO_SIZE_LIMITS
from app.models.schemas import ConvertedEmoji, EmojiResult

GIF_SIZE = (256, 256)
KAKAO_GIF_SIZE = (360, 360)
NUM_FRAMES = 12


@dataclass
class MotionPreset:
    """감정별 모션 파라미터."""

    y_amplitude: float  # 상하 이동 크기 (px)
    y_speed: float  # 상하 이동 속도 배율
    stretch_amount: float  # 세로 스트레치 비율 (0.0 ~ 0.15)
    squash_amount: float  # 가로 스쿼시 비율 (0.0 ~ 0.15)
    rotation_deg: float  # 최대 회전 각도
    rotation_speed: float  # 회전 속도 배율
    scale_pulse: float  # 전체 크기 맥동 비율 (0.0 ~ 0.15)
    frame_duration: int  # 프레임 간격 (ms)


MOTION_PRESETS: dict[str, MotionPreset] = {
    # 신나게 통통 튀기 + 좌우 흔들림
    "happy": MotionPreset(
        y_amplitude=10,
        y_speed=2.0,
        stretch_amount=0.08,
        squash_amount=0.06,
        rotation_deg=5.0,
        rotation_speed=2.0,
        scale_pulse=0.0,
        frame_duration=100,
    ),
    # 축 처지며 느리게 고개 숙임
    "sad": MotionPreset(
        y_amplitude=3,
        y_speed=0.5,
        stretch_amount=0.03,
        squash_amount=0.02,
        rotation_deg=2.0,
        rotation_speed=0.5,
        scale_pulse=0.0,
        frame_duration=180,
    ),
    # 빠르게 부들부들 떨림
    "angry": MotionPreset(
        y_amplitude=2,
        y_speed=4.0,
        stretch_amount=0.02,
        squash_amount=0.04,
        rotation_deg=1.5,
        rotation_speed=6.0,
        scale_pulse=0.03,
        frame_duration=60,
    ),
    # 느린 호흡 (천천히 오르내림)
    "sleepy": MotionPreset(
        y_amplitude=4,
        y_speed=0.5,
        stretch_amount=0.05,
        squash_amount=0.03,
        rotation_deg=1.5,
        rotation_speed=0.5,
        scale_pulse=0.02,
        frame_duration=200,
    ),
    # 두근두근 심장 박동
    "love": MotionPreset(
        y_amplitude=3,
        y_speed=1.0,
        stretch_amount=0.02,
        squash_amount=0.02,
        rotation_deg=2.0,
        rotation_speed=1.0,
        scale_pulse=0.08,
        frame_duration=120,
    ),
    # 깜짝 놀라 점프 + 착지 스쿼시
    "surprised": MotionPreset(
        y_amplitude=14,
        y_speed=1.0,
        stretch_amount=0.10,
        squash_amount=0.08,
        rotation_deg=0.0,
        rotation_speed=0.0,
        scale_pulse=0.0,
        frame_duration=100,
    ),
    # 여유롭게 좌우 스웨이
    "cool": MotionPreset(
        y_amplitude=2,
        y_speed=0.8,
        stretch_amount=0.02,
        squash_amount=0.02,
        rotation_deg=4.0,
        rotation_speed=1.0,
        scale_pulse=0.0,
        frame_duration=150,
    ),
    # 점프하며 좌우 회전
    "celebrate": MotionPreset(
        y_amplitude=12,
        y_speed=1.5,
        stretch_amount=0.06,
        squash_amount=0.05,
        rotation_deg=8.0,
        rotation_speed=1.5,
        scale_pulse=0.04,
        frame_duration=100,
    ),
}

DEFAULT_PRESET = MotionPreset(
    y_amplitude=6,
    y_speed=1.0,
    stretch_amount=0.06,
    squash_amount=0.04,
    rotation_deg=3.0,
    rotation_speed=1.0,
    scale_pulse=0.0,
    frame_duration=120,
)


def _get_preset(emotion: str) -> MotionPreset:
    """감정 문자열에서 가장 가까운 프리셋 반환."""
    lower = emotion.lower()
    for key, preset in MOTION_PRESETS.items():
        if key in lower:
            return preset
    return DEFAULT_PRESET


# 배경 판정 임계값 (흰색/투명 배경 감지)
_BG_THRESHOLD = 240
_ALPHA_THRESHOLD = 30


def _detect_character_bbox(
    img: Image.Image,
    padding: int = 4,
) -> tuple[int, int, int, int]:
    """캐릭터(비배경) 영역의 바운딩 박스 감지.

    RGBA → 알파 채널 기반, RGB → 흰색 배경 기반으로 전경 영역을 찾는다.
    반환: (left, top, right, bottom)
    """
    if img.mode == "RGBA":
        alpha = img.split()[3]
        bbox = alpha.point(lambda p: 255 if p > _ALPHA_THRESHOLD else 0).getbbox()
    else:
        # RGB: 흰색이 아닌 픽셀을 전경으로 판단
        r, g, b = img.split()[:3]
        mask = Image.merge(
            "L",
            [r.point(lambda p: 0 if p > _BG_THRESHOLD else 255)],
        )
        for ch in (g, b):
            ch_mask = ch.point(lambda p: 0 if p > _BG_THRESHOLD else 255)
            mask = Image.composite(
                Image.new("L", img.size, 255),
                mask,
                ch_mask,
            )
        bbox = mask.getbbox()

    if not bbox:
        return (0, 0, img.width, img.height)

    # 패딩 추가
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(img.width, bbox[2] + padding)
    bottom = min(img.height, bbox[3] + padding)
    return (left, top, right, bottom)


def _find_pivot(bbox: tuple[int, int, int, int]) -> tuple[int, int]:
    """캐릭터 bbox의 하단 중앙 (발 위치)을 피벗으로 사용."""
    left, top, right, bottom = bbox
    return ((left + right) // 2, bottom)


def _has_scene_background(img: Image.Image) -> bool:
    """이미지가 장면 배경(비흰색)을 가지고 있는지 판단."""
    if img.mode == "RGBA":
        alpha = img.split()[3]
        # 투명 픽셀이 10% 이상이면 투명 배경
        transparent_ratio = sum(1 for p in alpha.getdata() if p < _ALPHA_THRESHOLD) / (
            img.width * img.height
        )
        if transparent_ratio > 0.1:
            return False

    # 가장자리 1px 샘플링해서 흰색인지 확인
    pixels = []
    for x in range(img.width):
        pixels.append(img.getpixel((x, 0))[:3])
        pixels.append(img.getpixel((x, img.height - 1))[:3])
    for y in range(img.height):
        pixels.append(img.getpixel((0, y))[:3])
        pixels.append(img.getpixel((img.width - 1, y))[:3])

    white_count = sum(
        1 for r, g, b in pixels if r > _BG_THRESHOLD and g > _BG_THRESHOLD and b > _BG_THRESHOLD
    )
    return white_count / len(pixels) < 0.7


def _extract_background(img: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    """캐릭터 영역을 지운 배경 이미지 생성 (간단한 인페인팅)."""
    bg = img.copy()
    left, top, right, bottom = bbox
    # 캐릭터 영역을 주변 색으로 채움
    # 간단하게: bbox 바깥 가장자리 색의 평균으로 채우기
    edge_pixels = []
    for x in range(left, right):
        if top > 0:
            edge_pixels.append(img.getpixel((x, max(0, top - 1)))[:3])
        if bottom < img.height:
            edge_pixels.append(img.getpixel((x, min(img.height - 1, bottom)))[:3])
    for y in range(top, bottom):
        if left > 0:
            edge_pixels.append(img.getpixel((max(0, left - 1), y))[:3])
        if right < img.width:
            edge_pixels.append(img.getpixel((min(img.width - 1, right), y))[:3])

    if edge_pixels:
        avg_r = sum(p[0] for p in edge_pixels) // len(edge_pixels)
        avg_g = sum(p[1] for p in edge_pixels) // len(edge_pixels)
        avg_b = sum(p[2] for p in edge_pixels) // len(edge_pixels)
        fill_color = (avg_r, avg_g, avg_b, 255)
    else:
        fill_color = (255, 255, 255, 255)

    from PIL import ImageDraw

    draw = ImageDraw.Draw(bg)
    draw.rectangle([left, top, right, bottom], fill=fill_color)
    return bg


def _create_emotion_frames(
    img: Image.Image,
    preset: MotionPreset,
    num_frames: int = NUM_FRAMES,
    size: tuple[int, int] = GIF_SIZE,
) -> list[Image.Image]:
    """캐릭터 bbox 기반 감정 애니메이션 프레임 생성.

    배경이 있는 이미지: 배경 고정 + 캐릭터만 움직임
    흰/투명 배경 이미지: 흰색 캔버스 + 캐릭터만 움직임
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    bbox = _detect_character_bbox(img)
    character = img.crop(bbox)
    pivot = _find_pivot(bbox)
    has_bg = _has_scene_background(img)

    bg_layer = _extract_background(img, bbox) if has_bg else None

    frames: list[Image.Image] = []

    for i in range(num_frames):
        t = i / num_frames
        angle = t * 2 * math.pi

        dy = int(-preset.y_amplitude * math.sin(angle * preset.y_speed))
        pulse = 1.0 + preset.scale_pulse * math.sin(angle * 2)
        stretch = pulse + preset.stretch_amount * math.sin(angle * preset.y_speed)
        squash = pulse - preset.squash_amount * math.sin(angle * preset.y_speed)

        new_w = max(1, int(character.width * squash))
        new_h = max(1, int(character.height * stretch))
        deformed = character.resize((new_w, new_h), Image.LANCZOS)

        if preset.rotation_deg > 0:
            rot = preset.rotation_deg * math.sin(angle * preset.rotation_speed)
            deformed = deformed.rotate(
                rot,
                resample=Image.BICUBIC,
                expand=True,
                fillcolor=(0, 0, 0, 0),
            )

        canvas = bg_layer.copy() if bg_layer else Image.new("RGBA", size, (255, 255, 255, 255))

        paste_x = pivot[0] - deformed.width // 2
        paste_y = pivot[1] - deformed.height + dy
        canvas.paste(deformed, (paste_x, paste_y), deformed)
        frames.append(canvas.convert("RGB"))

    return frames


def convert_gif(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """감정에 맞는 자연스러운 모션으로 GIF 변환."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(GIF_SIZE, Image.LANCZOS)

        preset = _get_preset(emoji.emotion)
        frames = _create_emotion_frames(img, preset)
        gif_url = encode_gif(frames, duration=preset.frame_duration)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=gif_url,
                format="gif",
                width=GIF_SIZE[0],
                height=GIF_SIZE[1],
            )
        )

    return results


def _optimize_gif_size(frames: list[Image.Image], max_bytes: int, duration: int) -> str:
    """GIF 용량 제한 내로 최적화. 초과 시 프레임 크기 축소.

    Raises:
        ValueError: 최소 스케일까지 축소해도 용량 초과 시
    """
    import base64

    gif_url = encode_gif(frames, duration=duration)
    b64_data = gif_url.split(",", 1)[1]
    raw = base64.b64decode(b64_data)

    if len(raw) <= max_bytes:
        return gif_url

    scale = 0.9
    max_attempts = 7
    for _ in range(max_attempts):
        new_size = (int(frames[0].width * scale), int(frames[0].height * scale))
        resized_frames = [f.resize(new_size, Image.LANCZOS) for f in frames]
        gif_url = encode_gif(resized_frames, duration=duration)
        b64_data = gif_url.split(",", 1)[1]
        raw = base64.b64decode(b64_data)
        if len(raw) <= max_bytes:
            return gif_url
        scale -= 0.1

    raise ValueError(
        f"GIF 최적화 실패: 최소 크기로 축소해도 용량 제한({max_bytes // 1024}KB)을 초과합니다"
    )


def convert_kakao_animated(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """카카오 움직이는 이모티콘 규격으로 감정별 GIF 변환 (360x360, ≤650KB)."""
    max_count = KAKAO_COUNT_LIMITS["animated"]
    if len(emojis) > max_count:
        raise ValueError(
            f"카카오 움직이는 이모티콘은 최대 {max_count}개입니다 (입력: {len(emojis)}개)"
        )

    max_bytes = KAKAO_SIZE_LIMITS["animated"]
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(KAKAO_GIF_SIZE, Image.LANCZOS)

        preset = _get_preset(emoji.emotion)
        frames = _create_emotion_frames(img, preset, size=KAKAO_GIF_SIZE)
        gif_url = _optimize_gif_size(frames, max_bytes, preset.frame_duration)

        results.append(
            ConvertedEmoji(
                emotion=emoji.emotion,
                image_url=gif_url,
                format="kakao_animated",
                width=KAKAO_GIF_SIZE[0],
                height=KAKAO_GIF_SIZE[1],
            )
        )

    return results
