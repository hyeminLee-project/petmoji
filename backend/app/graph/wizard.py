"""LangGraph 위자드 그래프 정의."""

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    analyze_node,
    detail_node,
    free_generate_node,
    generate_node,
    proportion_node,
    reference_node,
    style_node,
)
from app.graph.state import WizardState


def _route_after_analyze(state: WizardState) -> str:
    """분석 후 티어에 따라 분기."""
    if state.get("tier") == "free":
        return "free_generate"
    return "style"


def _route_step(state: WizardState) -> str:
    """현재 단계에 따라 다음 노드 라우팅."""
    step = state.get("current_step", "style")
    step_map = {
        "style": "style",
        "proportion": "proportion",
        "detail": "detail",
        "reference": "reference",
        "generate": "generate",
    }
    return step_map.get(step, "style")


def build_wizard_graph() -> StateGraph:
    """위자드 그래프 빌드."""
    graph = StateGraph(WizardState)

    # 노드 등록
    graph.add_node("analyze", analyze_node)
    graph.add_node("style", style_node)
    graph.add_node("proportion", proportion_node)
    graph.add_node("detail", detail_node)
    graph.add_node("reference", reference_node)
    graph.add_node("generate", generate_node)
    graph.add_node("free_generate", free_generate_node)

    # 엣지
    graph.set_entry_point("analyze")
    graph.add_conditional_edges("analyze", _route_after_analyze)
    graph.add_edge("style", END)  # step별 호출이므로 각 노드는 END로
    graph.add_edge("proportion", END)
    graph.add_edge("detail", END)
    graph.add_edge("reference", END)
    graph.add_edge("generate", END)
    graph.add_edge("free_generate", END)

    return graph


# 앱 수준 싱글턴 (서버 실행 시 사용)
_app_graph = None
_app_ctx = None
_app_checkpointer = None


async def get_app_wizard_graph():
    """앱 수명 동안 유지되는 싱글턴 그래프."""
    global _app_graph, _app_ctx, _app_checkpointer

    if _app_graph is None:
        _app_ctx = AsyncSqliteSaver.from_conn_string(":memory:")
        _app_checkpointer = await _app_ctx.__aenter__()
        graph = build_wizard_graph()
        _app_graph = graph.compile(checkpointer=_app_checkpointer)

    return _app_graph


async def shutdown_wizard_graph() -> None:
    """앱 종료 시 체크포인터 리소스 정리."""
    global _app_graph, _app_ctx, _app_checkpointer

    if _app_ctx is not None:
        await _app_ctx.__aexit__(None, None, None)
    _app_graph = None
    _app_ctx = None
    _app_checkpointer = None
