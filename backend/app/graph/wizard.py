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


# 싱글턴 체크포인터 + 컴파일된 그래프
_checkpointer = None
_compiled_graph = None


async def get_wizard_graph():
    """체크포인터가 설정된 컴파일 그래프 반환."""
    global _checkpointer, _compiled_graph

    if _compiled_graph is None:
        _checkpointer = AsyncSqliteSaver.from_conn_string(":memory:")
        await _checkpointer.setup()
        graph = build_wizard_graph()
        _compiled_graph = graph.compile(checkpointer=_checkpointer)

    return _compiled_graph
