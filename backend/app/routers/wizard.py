"""위자드 API 엔드포인트 — LangGraph 기반 단계별 가이드."""

import asyncio
import contextlib
import hashlib
import hmac
import logging
import os
import secrets
import tempfile
import time
import uuid

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.converters.base import decode_image, encode_image
from app.graph.callbacks import SSECallback
from app.graph.nodes import (
    detail_node,
    proportion_node,
    reference_node,
    scene_node,
    style_node,
)
from app.graph.prompts import build_wizard_prompt
from app.graph.wizard import get_app_wizard_graph
from app.models.schemas import (
    WizardBackRequest,
    WizardBackResponse,
    WizardGenerateRequest,
    WizardStartResponse,
    WizardStepRequest,
)
from app.models.tiers import TierType, get_tier_config
from app.services.caption import generate_captions
from app.services.generator import EMOTIONS, PROVIDERS
from app.services.overlay import overlay_caption
from app.utils.upload import read_and_validate_image

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/wizard")

# 세션 TTL: 30분
SESSION_TTL_SECONDS = 30 * 60
MAX_SESSIONS = 1000
# 백그라운드 정리 주기: 5분
CLEANUP_INTERVAL_SECONDS = 5 * 60

# 세션 토큰 서명용 비밀키 (프로세스 시작 시 생성)
_SESSION_SECRET = secrets.token_bytes(32)

# 세션별 이미지 경로 + 생성 시간 저장
_session_images: dict[str, str] = {}
_session_created: dict[str, float] = {}
_session_tokens: dict[str, str] = {}

_cleanup_task: asyncio.Task | None = None


def _generate_session_token(session_id: str) -> str:
    """세션 ID 기반 HMAC 토큰 생성."""
    return hmac.new(_SESSION_SECRET, session_id.encode(), hashlib.sha256).hexdigest()


def _verify_session_token(session_id: str, token: str | None) -> None:
    """세션 토큰 검증. 실패 시 HTTPException."""
    if not token:
        raise HTTPException(status_code=401, detail="세션 토큰이 필요합니다")
    expected = _session_tokens.get(session_id)
    if not expected or not hmac.compare_digest(expected, token):
        raise HTTPException(status_code=403, detail="유효하지 않은 세션 토큰입니다")

    # 세션 만료 체크
    created = _session_created.get(session_id)
    if not created or time.time() - created > SESSION_TTL_SECONDS:
        _remove_session(session_id)
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다")


def _remove_session(session_id: str) -> None:
    """단일 세션 정리."""
    tmp_path = _session_images.pop(session_id, None)
    if tmp_path:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
    _session_created.pop(session_id, None)
    _session_tokens.pop(session_id, None)


def _cleanup_expired_sessions() -> None:
    """만료된 세션의 임시 파일 삭제 및 메모리 정리."""
    now = time.time()
    expired = [
        sid for sid, created in _session_created.items() if now - created > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _remove_session(sid)
    if expired:
        logger.info("Cleaned up %d expired wizard sessions", len(expired))


async def _periodic_cleanup() -> None:
    """백그라운드에서 주기적으로 만료 세션 정리."""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            _cleanup_expired_sessions()
        except Exception:
            logger.exception("Session cleanup failed")


def start_cleanup_task() -> None:
    """앱 시작 시 호출하여 백그라운드 정리 태스크 시작."""
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_periodic_cleanup())


async def stop_cleanup_task() -> None:
    """앱 종료 시 호출하여 백그라운드 정리 태스크 취소 + 남은 세션 정리."""
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _cleanup_task
        _cleanup_task = None

    # 남은 세션의 임시 파일 모두 정리
    for sid in list(_session_images):
        _remove_session(sid)


@router.post("/start")
@limiter.limit("5/minute")
async def wizard_start(
    request: Request,
    file: UploadFile = File(...),
    tier: TierType = Form("free"),
    provider: str = Form("gemini"),
    analyzer: str = Form("gemini"),
):
    """위자드 세션 시작 + 사진 분석."""
    # 만료된 세션 정리
    _cleanup_expired_sessions()

    # 세션 수 제한 (DoS 방지)
    if len(_session_images) >= MAX_SESSIONS:
        raise HTTPException(status_code=503, detail="서버가 바쁩니다. 잠시 후 다시 시도해주세요.")

    # 입력 검증 (매직 바이트 기반 파일 타입 검증 + 크기 제한)
    image_bytes, content_type = await read_and_validate_image(file)

    # 이미지를 임시 파일에 저장
    session_id = str(uuid.uuid4())
    tmp_path = os.path.join(tempfile.gettempdir(), f"petmoji_{session_id}")
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)
    _session_images[session_id] = tmp_path
    _session_created[session_id] = time.time()

    # 세션 토큰 생성
    session_token = _generate_session_token(session_id)
    _session_tokens[session_id] = session_token

    # LangGraph 실행: analyze 노드
    graph = await get_app_wizard_graph()
    config = {"configurable": {"thread_id": session_id}}

    initial_state = {
        "session_id": session_id,
        "tier": tier,
        "image_path": tmp_path,
        "content_type": content_type,
        "provider": provider,
        "analyzer": analyzer,
        "previews": {},
        "emojis": [],
        "style": "2d",
        "proportion": "chibi",
        "detail": {"eye_size": "big", "outline": "bold", "background": "white"},
        "reference": "none",
        "custom_prompt": "",
        "accessory": "none",
        "scene_background": "white",
        "time_of_day": "none",
        "emoji_count": get_tier_config(tier)["max_emotions"],
    }

    result = await graph.ainvoke(initial_state, config)

    return WizardStartResponse(
        session_id=session_id,
        session_token=session_token,
        pet_features=result["pet_features"],
        tier_config=get_tier_config(tier),
    )


@router.post("/step")
@limiter.limit("20/minute")
async def wizard_step(
    request: Request,
    body: WizardStepRequest,
    x_session_token: str | None = Header(None),
):
    """위자드 단계 실행 + 미리보기 생성 (SSE)."""
    _verify_session_token(body.session_id, x_session_token)

    graph = await get_app_wizard_graph()
    config = {"configurable": {"thread_id": body.session_id}}

    # 현재 상태 가져오기
    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    current_state = state.values

    # 티어 검증: 무료 사용자는 위자드 사용 불가
    if current_state.get("tier") == "free":
        raise HTTPException(
            status_code=403, detail="위자드는 프리미엄 이상 티어에서 사용 가능합니다"
        )

    # 선택값 적용
    step = body.step
    selection = body.selection

    update = {"current_step": step}
    if step == "style":
        update["style"] = selection.get("style", "2d")
    elif step == "proportion":
        update["proportion"] = selection.get("proportion", "chibi")
    elif step == "detail":
        update["detail"] = selection.get("detail", {})
    elif step == "reference":
        update["reference"] = selection.get("reference", "none")
    elif step == "scene":
        scene_sel = selection.get("scene", {})
        update["accessory"] = scene_sel.get("accessory", "none")
        update["scene_background"] = scene_sel.get("scene_background", "white")
        update["time_of_day"] = scene_sel.get("time_of_day", "none")

    # 상태 업데이트
    await graph.aupdate_state(config, update)

    # 노드 함수 매핑
    node_fns = {
        "style": style_node,
        "proportion": proportion_node,
        "detail": detail_node,
        "reference": reference_node,
        "scene": scene_node,
    }
    node_fn = node_fns.get(step)
    if not node_fn:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 단계: {step}")

    callback = SSECallback()

    async def run_and_stream():
        try:
            await callback.emit(
                "progress",
                {
                    "step": step,
                    "message": f"{step} 미리보기 생성 중...",
                    "progress": 0.3,
                },
            )

            # 현재 상태를 가져와 노드 함수를 직접 실행
            updated_state = await graph.aget_state(config)
            node_result = await node_fn(updated_state.values)

            # 결과를 그래프 상태에 반영
            await graph.aupdate_state(config, node_result)

            preview_url = node_result.get("previews", {}).get(step, "")
            await callback.emit(
                "preview",
                {
                    "step": step,
                    "image_url": preview_url,
                },
            )
        except Exception:
            logger.exception("Wizard step failed: %s", step)
            await callback.emit("error", {"message": f"{step} 단계 처리 실패"})
        finally:
            await callback.done()

    asyncio.create_task(run_and_stream())

    return StreamingResponse(
        callback.stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/back", response_model=WizardBackResponse)
@limiter.limit("15/minute")
async def wizard_back(
    request: Request,
    body: WizardBackRequest,
    x_session_token: str | None = Header(None),
):
    """이전 단계로 이동 (이미지 재생성 없이 기존 미리보기 반환)."""
    _verify_session_token(body.session_id, x_session_token)

    graph = await get_app_wizard_graph()
    config = {"configurable": {"thread_id": body.session_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 단계를 되돌림
    await graph.aupdate_state(config, {"current_step": body.target_step})

    updated_state = await graph.aget_state(config)
    previews = updated_state.values.get("previews", {})

    return WizardBackResponse(
        current_step=body.target_step,
        previews=previews,
    )


@router.post("/generate")
@limiter.limit("5/minute")
async def wizard_generate(
    request: Request,
    body: WizardGenerateRequest,
    x_session_token: str | None = Header(None),
):
    """전체 이모지 세트 생성 (SSE)."""
    _verify_session_token(body.session_id, x_session_token)

    graph = await get_app_wizard_graph()
    config = {"configurable": {"thread_id": body.session_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # emoji_count 업데이트
    await graph.aupdate_state(
        config,
        {"current_step": "generate", "emoji_count": body.emoji_count},
    )

    callback = SSECallback()

    async def run_and_stream():
        try:
            updated_state = await graph.aget_state(config)
            state = updated_state.values
            emoji_count = state.get("emoji_count", 8)
            generate_fn = PROVIDERS[state.get("provider", "gemini")]

            from app.graph.nodes import _truncate_custom_prompt

            base_prompt = build_wizard_prompt(
                pet_features=state.get("pet_features", {}),
                style=state.get("style", "2d"),
                proportion=state.get("proportion", "chibi"),
                detail=state.get("detail"),
                reference=state.get("reference", "none"),
                custom_prompt=_truncate_custom_prompt(state),
                accessory=state.get("accessory", "none"),
                scene_background=state.get("scene_background", "white"),
                time_of_day=state.get("time_of_day", "none"),
            )

            emotions_to_generate = EMOTIONS[:emoji_count]

            # 캡션 생성
            captions: dict[str, str] = {}
            pet_features_obj = state.get("pet_features")
            if pet_features_obj:
                await callback.emit(
                    "progress",
                    {
                        "step": "captioning",
                        "message": "캐릭터 대사를 만들고 있어요...",
                        "progress": 0.05,
                    },
                )
                try:
                    from app.models.schemas import PetFeatures

                    if isinstance(pet_features_obj, dict):
                        pet_features_obj = PetFeatures(**pet_features_obj)
                    captions = await generate_captions(
                        emotions_to_generate, pet_features_obj, state.get("provider", "gemini")
                    )
                except Exception:
                    logger.warning("Caption generation failed in wizard, continuing without")

            emojis = []

            for i, (emotion, description) in enumerate(emotions_to_generate):
                await callback.emit(
                    "progress",
                    {
                        "step": "generating",
                        "message": f"{emotion} 생성 중... ({i + 1}/{len(emotions_to_generate)})",
                        "progress": (i + 1) / len(emotions_to_generate),
                    },
                )

                prompt = f"""{base_prompt}
Expression/pose: {emotion} - {description}.
No text, no watermark, clean background."""

                image_url = await generate_fn(prompt)

                # 캡션 오버레이
                if captions and emotion in captions and captions[emotion]:
                    img = decode_image(image_url)
                    img = overlay_caption(img, captions[emotion])
                    image_url = encode_image(img)

                emojis.append({"emotion": emotion, "image_url": image_url})

                await callback.emit(
                    "emoji",
                    {
                        "emotion": emotion,
                        "image_url": image_url,
                        "index": i,
                        "total": len(emotions_to_generate),
                    },
                )

            # 결과를 그래프 상태에 반영
            await graph.aupdate_state(config, {"emojis": emojis})

            await callback.emit(
                "complete",
                {
                    "pet_features": state.get("pet_features", {}),
                    "emojis": emojis,
                },
            )
        except Exception:
            logger.exception("Wizard generate failed")
            await callback.emit("error", {"message": "이모지 생성 중 오류가 발생했습니다"})
        finally:
            await callback.done()

    asyncio.create_task(run_and_stream())

    return StreamingResponse(
        callback.stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
