from __future__ import annotations

from langgraph.graph import StateGraph, END

from .agents import (
    data_loader_agent,
    entity_resolver_agent,
    omnichannel_agent,
    query_analyzer_agent,
    traversal_agent,
)
from .state import GraphState


_graph = None


def _router(state: GraphState) -> str:
    return state.get("mode", "retrieve")


def build_graph():
    global _graph
    if _graph:
        return _graph

    workflow = StateGraph(GraphState)
    workflow.add_node("query_analyzer", query_analyzer_agent)
    workflow.add_node("entity_resolver", entity_resolver_agent)
    workflow.add_node("data_loader", data_loader_agent)
    workflow.add_node("traversal", traversal_agent)
    workflow.add_node("omnichannel", omnichannel_agent)

    workflow.set_entry_point("query_analyzer")
    workflow.add_edge("query_analyzer", "entity_resolver")
    workflow.add_conditional_edges(
        "entity_resolver",
        _router,
        {
            "ingest": "data_loader",
            "retrieve": "traversal",
        },
    )
    workflow.add_edge("data_loader", "omnichannel")
    workflow.add_edge("traversal", "omnichannel")
    workflow.add_edge("omnichannel", END)

    _graph = workflow.compile()
    return _graph
