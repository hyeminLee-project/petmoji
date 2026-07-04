"""움직이는 이모지 GIF 변환기.

감정별 자연스러운 모션을 적용하여 GIF 애니메이션 생성.
- 이징 함수로 자연스러운 가감속
- 감정별 고유한 모션 커브 (바운스, 탄성, 호흡 등)
- 20프레임으로 부드러운 움직임

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
from app.services.overlay import render_caption_layer

GIF_SIZE = (256, 256)
KAKAO_GIF_SIZE = (360, 360)
NUM_FRAMES = 20


# ---------------------------------------------------------------------------
# 이징 함수 (0.0~1.0 입력 → 0.0~1.0 출력)
# ---------------------------------------------------------------------------


def _ease_in_out_sine(t: float) -> float:
    """부드러운 시작과 끝."""
    return -(math.cos(math.pi * t) - 1) / 2


def _ease_out_bounce(t: float) -> float:
    """통통 튀는 바운스."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def _ease_out_elastic(t: float) -> float:
    """탄성 있는 스프링."""
    if t == 0 or t == 1:
        return t
    return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def _ease_in_out_quad(t: float) -> float:
    """부드러운 가감속."""
    if t < 0.5:
        return 2 * t * t
    return 1 - math.pow(-2 * t + 2, 2) / 2


# ---------------------------------------------------------------------------
# 감정별 모션 프리셋
# ---------------------------------------------------------------------------


@dataclass
class MotionPreset:
    """감정별 모션 파라미터."""

    y_amplitude: float  # 상하 이동 크기 (px)
    stretch_amount: float  # 세로 스트레치 비율 (0.0 ~ 0.15)
    squash_amount: float  # 가로 스쿼시 비율 (0.0 ~ 0.15)
    rotation_deg: float  # 최대 회전 각도
    scale_pulse: float  # 전체 크기 맥동 비율 (0.0 ~ 0.15)
    frame_duration: int  # 프레임 간격 (ms)
    x_amplitude: float = 0.0  # 좌우 이동 크기 (px)
    # 모션 커브: 프레임 인덱스(0~1) → 각 축의 값(0~1)을 계산하는 방식 지정
    motion_type: str = "sine"  # sine, bounce, breathe, shake, jump, sway, heartbeat


MOTION_PRESETS: dict[str, MotionPreset] = {
    # 신나게 통통 튀기 (바운스 이징)
    "happy": MotionPreset(
        y_amplitude=14,
        stretch_amount=0.10,
        squash_amount=0.08,
        rotation_deg=5.0,
        scale_pulse=0.0,
        frame_duration=80,
        x_amplitude=3.0,
        motion_type="bounce",
    ),
    # 축 처지며 느리게 흔들림 (부드러운 호흡)
    "sad": MotionPreset(
        y_amplitude=3,
        stretch_amount=0.02,
        squash_amount=0.01,
        rotation_deg=3.0,
        scale_pulse=0.0,
        frame_duration=150,
        motion_type="breathe",
    ),
    # 빠르게 부들부들 (랜덤 쉐이크)
    "angry": MotionPreset(
        y_amplitude=3,
        stretch_amount=0.03,
        squash_amount=0.05,
        rotation_deg=2.0,
        scale_pulse=0.04,
        frame_duration=50,
        x_amplitude=4.0,
        motion_type="shake",
    ),
    # 느린 호흡 (천천히 오르내림)
    "sleepy": MotionPreset(
        y_amplitude=4,
        stretch_amount=0.04,
        squash_amount=0.02,
        rotation_deg=2.0,
        scale_pulse=0.03,
        frame_duration=160,
        motion_type="breathe",
    ),
    # 두근두근 심장 박동 (확대-축소)
    "love": MotionPreset(
        y_amplitude=3,
        stretch_amount=0.02,
        squash_amount=0.02,
        rotation_deg=3.0,
        scale_pulse=0.10,
        frame_duration=100,
        motion_type="heartbeat",
    ),
    # 깜짝 놀라 점프 + 착지 (점프 커브)
    "surprised": MotionPreset(
        y_amplitude=18,
        stretch_amount=0.12,
        squash_amount=0.10,
        rotation_deg=0.0,
        scale_pulse=0.0,
        frame_duration=70,
        motion_type="jump",
    ),
    # 여유롭게 좌우 스웨이
    "cool": MotionPreset(
        y_amplitude=2,
        stretch_amount=0.02,
        squash_amount=0.02,
        rotation_deg=6.0,
        scale_pulse=0.0,
        frame_duration=120,
        x_amplitude=5.0,
        motion_type="sway",
    ),
    # 점프하며 회전 (바운스 + 회전)
    "celebrate": MotionPreset(
        y_amplitude=16,
        stretch_amount=0.08,
        squash_amount=0.06,
        rotation_deg=10.0,
        scale_pulse=0.05,
        frame_duration=70,
        x_amplitude=3.0,
        motion_type="bounce",
    ),
    # 흔들흔들 인사
    "greeting": MotionPreset(
        y_amplitude=4,
        stretch_amount=0.03,
        squash_amount=0.02,
        rotation_deg=8.0,
        scale_pulse=0.0,
        frame_duration=90,
        motion_type="sway",
    ),
    # 부끄러워서 움찔움찔
    "shy": MotionPreset(
        y_amplitude=3,
        stretch_amount=0.04,
        squash_amount=0.03,
        rotation_deg=4.0,
        scale_pulse=0.0,
        frame_duration=120,
        x_amplitude=2.0,
        motion_type="breathe",
    ),
    # 달려~!
    "running": MotionPreset(
        y_amplitude=8,
        stretch_amount=0.06,
        squash_amount=0.04,
        rotation_deg=3.0,
        scale_pulse=0.0,
        frame_duration=60,
        x_amplitude=6.0,
        motion_type="bounce",
    ),
    # 냠냠 먹기
    "eating": MotionPreset(
        y_amplitude=3,
        stretch_amount=0.06,
        squash_amount=0.04,
        rotation_deg=2.0,
        scale_pulse=0.0,
        frame_duration=100,
        motion_type="bounce",
    ),
    # 흑흑 울기 (떨림)
    "crying": MotionPreset(
        y_amplitude=4,
        stretch_amount=0.03,
        squash_amount=0.02,
        rotation_deg=2.0,
        scale_pulse=0.0,
        frame_duration=100,
        x_amplitude=3.0,
        motion_type="shake",
    ),
    # 신남 (빠른 바운스)
    "excited": MotionPreset(
        y_amplitude=12,
        stretch_amount=0.08,
        squash_amount=0.06,
        rotation_deg=6.0,
        scale_pulse=0.03,
        frame_duration=70,
        x_amplitude=4.0,
        motion_type="bounce",
    ),
}

DEFAULT_PRESET = MotionPreset(
    y_amplitude=6,
    stretch_amount=0.05,
    squash_amount=0.03,
    rotation_deg=3.0,
    scale_pulse=0.0,
    frame_duration=100,
    motion_type="sine",
)


def _get_preset(emotion: str) -> MotionPreset:
    """감정 문자열에서 가장 가까운 프리셋 반환."""
    lower = emotion.lower()
    for key, preset in MOTION_PRESETS.items():
        if key in lower:
            return preset
    return DEFAULT_PRESET


# ---------------------------------------------------------------------------
# 모션 계산
# ---------------------------------------------------------------------------


def _compute_motion(t: float, preset: MotionPreset) -> dict:
    """프레임 시간 t(0~1)에서 모션 값 계산.

    Returns:
        dy, dx, stretch, squash, rotation, scale
    """
    motion = preset.motion_type

    if motion == "bounce":
        # 위로 올라갔다가 바운스하며 착지
        # 전반: 올라감, 후반: 바운스 착지
        if t < 0.4:
            # 올라가는 구간 (이즈인아웃)
            up_t = t / 0.4
            eased = _ease_in_out_sine(up_t)
            dy = -preset.y_amplitude * eased
            stretch = 1.0 + preset.stretch_amount * eased
            squash = 1.0 - preset.squash_amount * eased * 0.5
        else:
            # 내려오며 바운스
            down_t = (t - 0.4) / 0.6
            eased = _ease_out_bounce(down_t)
            dy = -preset.y_amplitude * (1.0 - eased)
            # 착지 시 스쿼시
            land_factor = max(0, 1.0 - abs(dy) / max(1, preset.y_amplitude))
            stretch = 1.0 - preset.squash_amount * land_factor
            squash = 1.0 + preset.squash_amount * land_factor * 0.8
        dx = preset.x_amplitude * math.sin(t * 2 * math.pi)
        rotation = preset.rotation_deg * math.sin(t * 2 * math.pi)
        scale = 1.0 + preset.scale_pulse * math.sin(t * 4 * math.pi)

    elif motion == "breathe":
        # 부드러운 호흡 (이즈인아웃 사인)
        dy = -preset.y_amplitude * math.sin(t * 2 * math.pi)
        dx = 0
        # 호흡: 들숨(늘어남) - 날숨(줄어듦)
        breath = _ease_in_out_sine(math.fmod(t * 2, 1.0))
        stretch = 1.0 + preset.stretch_amount * breath
        squash = 1.0 - preset.squash_amount * breath * 0.5
        rotation = preset.rotation_deg * math.sin(t * math.pi)  # 한 방향으로 기울었다 돌아옴
        scale = 1.0 + preset.scale_pulse * breath

    elif motion == "shake":
        # 빠르게 부들부들 (고주파 + 감쇠 없는 진동)
        # 불규칙하게 보이도록 두 주파수 합성
        shake_y = math.sin(t * 8 * math.pi) + 0.5 * math.sin(t * 13 * math.pi)
        shake_x = math.cos(t * 7 * math.pi) + 0.3 * math.cos(t * 11 * math.pi)
        dy = preset.y_amplitude * shake_y / 1.5
        dx = preset.x_amplitude * shake_x / 1.3
        stretch = 1.0 + preset.stretch_amount * abs(math.sin(t * 6 * math.pi))
        squash = 1.0 + preset.squash_amount * abs(math.cos(t * 6 * math.pi))
        rotation = preset.rotation_deg * math.sin(t * 10 * math.pi)
        scale = 1.0 + preset.scale_pulse * abs(math.sin(t * 4 * math.pi))

    elif motion == "jump":
        # 점프: 웅크림 → 도약 → 체공 → 착지 스쿼시
        if t < 0.15:
            # 웅크림 (anticipation)
            squat_t = t / 0.15
            eased = _ease_in_out_quad(squat_t)
            dy = preset.y_amplitude * 0.15 * eased  # 살짝 아래로
            stretch = 1.0 - preset.stretch_amount * 0.5 * eased
            squash = 1.0 + preset.squash_amount * 0.5 * eased
        elif t < 0.55:
            # 도약 + 체공
            fly_t = (t - 0.15) / 0.4
            # 포물선: 0 → 1 → 0
            arc = 4 * fly_t * (1 - fly_t)
            dy = -preset.y_amplitude * arc
            stretch = 1.0 + preset.stretch_amount * arc
            squash = 1.0 - preset.squash_amount * arc * 0.3
        else:
            # 착지 + 바운스
            land_t = (t - 0.55) / 0.45
            eased = _ease_out_elastic(land_t)
            dy = 0
            # 착지 충격 → 복원
            impact = 1.0 - eased
            stretch = 1.0 - preset.squash_amount * impact
            squash = 1.0 + preset.squash_amount * impact * 0.8
        dx = 0
        rotation = 0
        scale = 1.0

    elif motion == "sway":
        # 좌우로 여유롭게 흔들림
        dx = preset.x_amplitude * math.sin(t * 2 * math.pi)
        dy = -preset.y_amplitude * abs(math.sin(t * 2 * math.pi))
        rotation = preset.rotation_deg * math.sin(t * 2 * math.pi)
        stretch = 1.0
        squash = 1.0
        scale = 1.0

    elif motion == "heartbeat":
        # 두근두근: 빠르게 커졌다 → 원래 → 다시 커졌다 → 원래 (이중 박동)
        # 1사이클에 2번 박동
        beat_t = math.fmod(t * 2, 1.0)
        if beat_t < 0.3:
            # 확장
            pulse = _ease_out_elastic(beat_t / 0.3)
        else:
            # 수축
            pulse = 1.0 - _ease_in_out_quad((beat_t - 0.3) / 0.7)
        scale = 1.0 + preset.scale_pulse * pulse
        dy = -preset.y_amplitude * pulse * 0.5
        dx = 0
        stretch = 1.0 + preset.stretch_amount * pulse
        squash = 1.0 - preset.squash_amount * pulse * 0.3
        rotation = preset.rotation_deg * math.sin(t * 4 * math.pi) * (1 - pulse * 0.5)

    else:  # sine (default)
        angle = t * 2 * math.pi
        dy = -preset.y_amplitude * math.sin(angle)
        dx = preset.x_amplitude * math.cos(angle)
        stretch = 1.0 + preset.stretch_amount * math.sin(angle)
        squash = 1.0 - preset.squash_amount * math.sin(angle)
        rotation = preset.rotation_deg * math.sin(angle)
        scale = 1.0 + preset.scale_pulse * math.sin(angle * 2)

    return {
        "dy": dy,
        "dx": dx,
        "stretch": stretch,
        "squash": squash,
        "rotation": rotation,
        "scale": scale,
    }


# ---------------------------------------------------------------------------
# 메시 워프 (부분 움직임)
# ---------------------------------------------------------------------------

# 강체 이동/회전 대신 발 고정 메시 워프를 적용할 모션
_WARP_MOTIONS = {"sway", "breathe", "shake"}
# 모션별 워프 진동 주기 (루프당 사이클 수, 정수여야 루프가 이어짐)
_WARP_FREQS = {"sway": 1.0, "breathe": 1.0, "shake": 4.0}
_WARP_STRIPS = 12


def _strip_dx(t: float, height_ratio: float, amplitude: float, freq: float) -> float:
    """높이 비율(발=0, 머리=1)에 따른 수평 변위.

    위로 갈수록 변위가 커지고(제곱 곡선) 반 박자 늦게 따라와서(위상 지연)
    상체가 출렁이는 follow-through가 생긴다.
    """
    factor = height_ratio**1.5
    delay = 0.12 * height_ratio / freq
    return amplitude * factor * math.sin(2 * math.pi * freq * (t - delay))


def _mesh_warp_character(
    img: Image.Image,
    t: float,
    amplitude: float,
    freq: float,
) -> Image.Image:
    """세로 그라디언트 메시 워프: 하단(발)은 고정, 위로 갈수록 크게 휘어진다.

    가로 스트립별로 소스 좌표를 밀어서 캐릭터가 연속적으로 휘어지게 한다.
    강체 변형과 달리 발이 바닥에 붙어 있어 부분 움직임처럼 보인다.
    """
    if amplitude < 0.5:
        return img

    pad = math.ceil(amplitude) + 2
    w, h = img.size
    padded = Image.new("RGBA", (w + pad * 2, h), (0, 0, 0, 0))
    padded.paste(img, (pad, 0))

    mesh = []
    for i in range(_WARP_STRIPS):
        y0 = h * i // _WARP_STRIPS
        y1 = h * (i + 1) // _WARP_STRIPS if i < _WARP_STRIPS - 1 else h
        dx0 = _strip_dx(t, 1 - y0 / h, amplitude, freq)
        dx1 = _strip_dx(t, 1 - y1 / h, amplitude, freq)
        bbox = (0, y0, padded.width, y1)
        quad = (
            -dx0,
            y0,
            -dx1,
            y1,
            padded.width - dx1,
            y1,
            padded.width - dx0,
            y0,
        )
        mesh.append((bbox, quad))

    return padded.transform(padded.size, Image.MESH, mesh, resample=Image.BICUBIC)


# ---------------------------------------------------------------------------
# 배경/캐릭터 감지
# ---------------------------------------------------------------------------

_BG_THRESHOLD = 240
_ALPHA_THRESHOLD = 30


def _detect_character_bbox(
    img: Image.Image,
    padding: int = 4,
) -> tuple[int, int, int, int]:
    """캐릭터(비배경) 영역의 바운딩 박스 감지."""
    if img.mode == "RGBA":
        alpha = img.split()[3]
        bbox = alpha.point(lambda p: 255 if p > _ALPHA_THRESHOLD else 0).getbbox()
    else:
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
        transparent_ratio = sum(1 for p in alpha.getdata() if p < _ALPHA_THRESHOLD) / (
            img.width * img.height
        )
        if transparent_ratio > 0.1:
            return False

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
    """캐릭터 영역을 테두리 평균색 사각형으로 채운 배경 이미지 생성."""
    bg = img.copy()
    left, top, right, bottom = bbox
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


# ---------------------------------------------------------------------------
# 프레임 생성
# ---------------------------------------------------------------------------


def _create_emotion_frames(
    img: Image.Image,
    preset: MotionPreset,
    num_frames: int = NUM_FRAMES,
    size: tuple[int, int] = GIF_SIZE,
    caption: str = "",
) -> list[Image.Image]:
    """캐릭터 bbox 기반 감정 애니메이션 프레임 생성.

    캡션은 캐릭터 모션과 분리하여 모든 프레임에 고정 위치로 합성한다.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    bbox = _detect_character_bbox(img)
    character = img.crop(bbox)
    pivot = _find_pivot(bbox)
    has_bg = _has_scene_background(img)

    bg_layer = _extract_background(img, bbox) if has_bg else None
    canvas_size = bg_layer.size if bg_layer else size
    caption_layer = render_caption_layer(canvas_size, caption)

    frames: list[Image.Image] = []

    for i in range(num_frames):
        t = i / num_frames
        m = _compute_motion(t, preset)

        dy = int(m["dy"])
        dx = int(m["dx"])
        scale_x = m["squash"] * m["scale"]
        scale_y = m["stretch"] * m["scale"]

        new_w = max(1, int(character.width * scale_x))
        new_h = max(1, int(character.height * scale_y))
        deformed = character.resize((new_w, new_h), Image.LANCZOS)

        if preset.motion_type in _WARP_MOTIONS:
            # 발 고정 메시 워프: 강체 이동/회전을 상체 스웨이로 대체
            amp = preset.x_amplitude * 2.0 + preset.rotation_deg * 0.8
            deformed = _mesh_warp_character(deformed, t, amp, _WARP_FREQS[preset.motion_type])
            dx = int(m["dx"] * 0.3)
        elif abs(m["rotation"]) > 0.1:
            deformed = deformed.rotate(
                m["rotation"],
                resample=Image.BICUBIC,
                expand=True,
                fillcolor=(0, 0, 0, 0),
            )

        canvas = bg_layer.copy() if bg_layer else Image.new("RGBA", size, (255, 255, 255, 255))

        paste_x = pivot[0] - deformed.width // 2 + dx
        paste_y = pivot[1] - deformed.height + dy
        canvas.paste(deformed, (paste_x, paste_y), deformed)
        if caption_layer is not None:
            canvas = Image.alpha_composite(canvas, caption_layer)
        frames.append(canvas.convert("RGB"))

    return frames


# ---------------------------------------------------------------------------
# 변환 API
# ---------------------------------------------------------------------------


def convert_gif(emojis: list[EmojiResult]) -> list[ConvertedEmoji]:
    """감정에 맞는 자연스러운 모션으로 GIF 변환."""
    results: list[ConvertedEmoji] = []

    for emoji in emojis:
        img = decode_image(emoji.image_url)
        img.thumbnail(GIF_SIZE, Image.LANCZOS)

        preset = _get_preset(emoji.emotion)
        frames = _create_emotion_frames(img, preset, caption=emoji.caption)
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


def _optimize_gif_size(
    frames: list[Image.Image], max_bytes: int, duration: int, transparent: bool = False
) -> str:
    """GIF 용량 제한 내로 최적화. 초과 시 프레임 크기 축소."""
    import base64

    gif_url = encode_gif(frames, duration=duration, transparent=transparent)
    b64_data = gif_url.split(",", 1)[1]
    raw = base64.b64decode(b64_data)

    if len(raw) <= max_bytes:
        return gif_url

    scale = 0.9
    max_attempts = 7
    for _ in range(max_attempts):
        new_size = (int(frames[0].width * scale), int(frames[0].height * scale))
        resized_frames = [f.resize(new_size, Image.LANCZOS) for f in frames]
        gif_url = encode_gif(resized_frames, duration=duration, transparent=transparent)
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
        frames = _create_emotion_frames(img, preset, size=KAKAO_GIF_SIZE, caption=emoji.caption)
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
