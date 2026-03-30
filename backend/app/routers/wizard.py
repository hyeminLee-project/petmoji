"""위자드 API 엔드포인트 — LangGraph 기반 단계별 가이드."""

import logging
import os
import tempfile
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.graph.callbacks import SSECallback
from app.graph.wizard import get_wizard_graph
from app.models.schemas import (
    WizardBackRequest,
    WizardBackResponse,
    WizardGenerateRequest,
    WizardStartResponse,
    WizardStepRequest,
)
from app.models.tiers import TierType, get_tier_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wizard")

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/heic"}

# 세션별 이미지 경로 저장
_session_images: dict[str, str] = {}


@router.post("/start", response_model=WizardStartResponse)
async def wizard_start(
    file: UploadFile = File(...),
    tier: TierType = Form("free"),
    provider: str = Form("gemini"),
    analyzer: str = Form("gemini"),
):
    """위자드 세션 시작 + 사진 분석."""
    # 입력 검증
    content_type = file.content_type or "image/jpeg"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식: {content_type}")

    image_bytes = await file.read()
    if not image_bytes or len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="파일이 비어있거나 10MB를 초과합니다")

    # 이미지를 임시 파일에 저장
    session_id = str(uuid.uuid4())
    tmp_path = os.path.join(tempfile.gettempdir(), f"petmoji_{session_id}")
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)
    _session_images[session_id] = tmp_path

    # LangGraph 실행: analyze 노드
    graph = await get_wizard_graph()
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
        "emoji_count": get_tier_config(tier)["max_emotions"],
    }

    result = await graph.ainvoke(initial_state, config)

    return WizardStartResponse(
        session_id=session_id,
        pet_features=result["pet_features"],
        tier_config=get_tier_config(tier),
    )


@router.post("/step")
async def wizard_step(request: WizardStepRequest):
    """위자드 단계 실행 + 미리보기 생성 (SSE)."""
    graph = await get_wizard_graph()
    config = {"configurable": {"thread_id": request.session_id}}

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
    step = request.step
    selection = request.selection

    update = {"current_step": step}
    if step == "style":
        update["style"] = selection.get("style", "2d")
    elif step == "proportion":
        update["proportion"] = selection.get("proportion", "chibi")
    elif step == "detail":
        update["detail"] = selection.get("detail", {})
    elif step == "reference":
        update["reference"] = selection.get("reference", "none")

    # 상태 업데이트 후 해당 노드 실행
    await graph.aupdate_state(config, update)

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

            result = await graph.ainvoke(None, config)

            preview_url = result.get("previews", {}).get(step, "")
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

    import asyncio

    asyncio.create_task(run_and_stream())

    return StreamingResponse(
        callback.stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.post("/back", response_model=WizardBackResponse)
async def wizard_back(request: WizardBackRequest):
    """이전 단계로 이동 (이미지 재생성 없이 기존 미리보기 반환)."""
    graph = await get_wizard_graph()
    config = {"configurable": {"thread_id": request.session_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # 단계를 되돌림
    await graph.aupdate_state(config, {"current_step": request.target_step})

    updated_state = await graph.aget_state(config)
    previews = updated_state.values.get("previews", {})

    return WizardBackResponse(
        current_step=request.target_step,
        previews=previews,
    )


@router.post("/generate")
async def wizard_generate(request: WizardGenerateRequest):
    """전체 이모지 세트 생성 (SSE)."""
    graph = await get_wizard_graph()
    config = {"configurable": {"thread_id": request.session_id}}

    state = await graph.aget_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    # emoji_count 업데이트 후 generate 노드 실행
    await graph.aupdate_state(
        config,
        {"current_step": "generate", "emoji_count": request.emoji_count},
    )

    callback = SSECallback()

    async def run_and_stream():
        try:
            await callback.emit(
                "progress",
                {
                    "step": "generating",
                    "message": "이모지 세트 생성을 시작합니다...",
                    "progress": 0.05,
                },
            )

            result = await graph.ainvoke(None, config)
            emojis = result.get("emojis", [])

            for i, emoji in enumerate(emojis):
                await callback.emit(
                    "emoji",
                    {
                        "emotion": emoji["emotion"],
                        "image_url": emoji["image_url"],
                        "index": i,
                        "total": len(emojis),
                    },
                )

            await callback.emit(
                "complete",
                {
                    "pet_features": result.get("pet_features", {}),
                    "emojis": emojis,
                },
            )
        except Exception:
            logger.exception("Wizard generate failed")
            await callback.emit("error", {"message": "이모지 생성 중 오류가 발생했습니다"})
        finally:
            await callback.done()

    import asyncio

    asyncio.create_task(run_and_stream())

    return StreamingResponse(
        callback.stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
