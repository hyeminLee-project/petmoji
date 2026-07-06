"""이모지 생성 스트리밍 코어 테스트"""

from app.services.generation_stream import stream_emoji_generation

EMOTIONS = [("happy", "smiling"), ("sad", "crying"), ("angry", "fuming")]


async def _collect(generation):
    return [event async for event in generation]


async def test_emits_progress_emoji_pairs_and_done():
    """이모지마다 progress+emoji 이벤트, 마지막에 done"""

    async def fake_generate(prompt: str) -> str:
        return "data:image/png;base64,xxx"

    async def fake_caption(image_url: str, emotion: str) -> str:
        return "좋아!" if emotion == "happy" else ""

    events = await _collect(
        stream_emoji_generation(
            base_prompt="base",
            suffix="No text.",
            emotions=EMOTIONS,
            generate_fn=fake_generate,
            caption_fn=fake_caption,
        )
    )

    types = [e for e, _ in events]
    assert types == ["progress", "emoji", "progress", "emoji", "progress", "emoji", "done"]

    done_payload = events[-1][1]
    assert [e["emotion"] for e in done_payload["emojis"]] == ["happy", "sad", "angry"]
    assert done_payload["emojis"][0]["caption"] == "좋아!"
    assert done_payload["emojis"][1]["caption"] == ""


async def test_no_caption_fn_yields_empty_captions():
    """caption_fn 미지정 시 캡션 없이 생성"""

    async def fake_generate(prompt: str) -> str:
        return "data:x"

    events = await _collect(
        stream_emoji_generation(
            base_prompt="base",
            suffix="s",
            emotions=EMOTIONS[:1],
            generate_fn=fake_generate,
        )
    )
    assert events[-1][1]["emojis"][0]["caption"] == ""


async def test_progress_respects_start_offset():
    """progress_start(선행 단계 구간)를 반영한 진행률"""

    async def fake_generate(prompt: str) -> str:
        return "data:x"

    events = await _collect(
        stream_emoji_generation(
            base_prompt="base",
            suffix="s",
            emotions=EMOTIONS[:2],
            generate_fn=fake_generate,
            progress_start=0.1,
        )
    )
    progresses = [p["progress"] for e, p in events if e == "progress"]
    assert progresses == [0.55, 1.0]


async def test_generation_failure_yields_error_and_stops():
    """생성 실패 시 error 이벤트 후 종료 (done 없음)"""

    async def failing_generate(prompt: str) -> str:
        raise RuntimeError("provider down")

    events = await _collect(
        stream_emoji_generation(
            base_prompt="base",
            suffix="s",
            emotions=EMOTIONS,
            generate_fn=failing_generate,
        )
    )
    assert events[-1][0] == "error"
    assert all(e != "done" for e, _ in events)


async def test_prompt_includes_emotion_and_suffix():
    """프롬프트에 감정 설명과 접미사가 포함됨"""
    seen_prompts: list[str] = []

    async def capture_generate(prompt: str) -> str:
        seen_prompts.append(prompt)
        return "data:x"

    await _collect(
        stream_emoji_generation(
            base_prompt="BASE",
            suffix="SUFFIX",
            emotions=[("happy", "smiling big")],
            generate_fn=capture_generate,
        )
    )
    assert len(seen_prompts) == 1
    assert "BASE" in seen_prompts[0]
    assert "happy - smiling big" in seen_prompts[0]
    assert seen_prompts[0].endswith("SUFFIX")
