from __future__ import annotations

from typing import List, Literal, TypedDict, Any, Optional


class GraphState(TypedDict, total=False):
    mode: Literal["ingest", "retrieve"]
    query: str
    text: str
    source: str
    intent: str
    entities: List[str]
    entity_graph: List[dict]
    relationships: List[dict]
    context: List[dict]
    response: str
    error: Optional[str]
    history: List[dict]
