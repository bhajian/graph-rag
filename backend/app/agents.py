from __future__ import annotations

import json
from typing import Any, Dict, List

import wikipedia

from .llm import get_llama_client
from .neo4j_client import query_graph, write_entities
from .state import GraphState


def _safe_json_loads(payload: str) -> Dict[str, Any]:
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        start = payload.find("{")
        end = payload.rfind("}")
        if start >= 0 and end >= 0:
            try:
                return json.loads(payload[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {}


def query_analyzer_agent(state: GraphState) -> GraphState:
    client = get_llama_client()
    user_text = state.get("text") if state.get("mode") == "ingest" else state.get("query")
    user_text = user_text or ""
    wiki_context = ""
    if state.get("mode") == "retrieve" and user_text:
        try:
            wiki_context = wikipedia.summary(user_text, sentences=3, auto_suggest=True)
        except Exception:
            wiki_context = ""

    system_prompt = """You are a query analyzer that determines the user's intent, key focus,
    and high-level entities for downstream knowledge graph tasks. Always output JSON with
    intent and entities fields."""
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "Mode: {mode}\nUser Input: {text}\nWikipedia Context: {wiki}\n"
            ).format(mode=state.get("mode"), text=user_text, wiki=wiki_context),
        },
    ]
    response = client.generate(messages, max_tokens=256)
    data = _safe_json_loads(response)
    entities = data.get("entities") or []
    if isinstance(entities, str):
        entities = [entities]
    state["intent"] = data.get("intent", "unknown")
    state["entities"] = [e.strip() for e in entities if isinstance(e, str)]
    return state


def entity_resolver_agent(state: GraphState) -> GraphState:
    client = get_llama_client()
    mode = state.get("mode")
    base_entities = state.get("entities", [])
    text = state.get("text") if mode == "ingest" else state.get("query")
    prompt = """You resolve entities and relationships for a knowledge graph.\n
    Return JSON with `entities` (list of objects with name and properties) and `relationships`
    (list of objects with start, end, type, properties). Ensure entities mentioned in the
    candidate list are grounded and disambiguated."""
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": (
                "Mode: {mode}\nCandidate entities: {entities}\nText: {text}\n"
            ).format(mode=mode, entities=base_entities, text=text),
        },
    ]
    response = client.generate(messages, max_tokens=512)
    payload = _safe_json_loads(response)
    state["entity_graph"] = payload.get("entities", [])
    state["relationships"] = payload.get("relationships", [])
    resolved_names = [entity.get("name") for entity in state["entity_graph"] if entity.get("name")]
    if resolved_names:
        state["entities"] = resolved_names
    return state


def data_loader_agent(state: GraphState) -> GraphState:
    if state.get("mode") != "ingest":
        return state
    entities = state.get("entity_graph") or []
    relationships = state.get("relationships") or []
    source = state.get("source")
    if source:
        for entity in entities:
            props = entity.setdefault("properties", {})
            props.setdefault("sources", [])
            if isinstance(props["sources"], list) and source not in props["sources"]:
                props["sources"].append(source)
    if entities:
        write_entities(entities, relationships)
    return state


def traversal_agent(state: GraphState) -> GraphState:
    if state.get("mode") != "retrieve":
        return state
    names = state.get("entities") or []
    traversed = query_graph(names)
    state["context"] = traversed
    return state


def omnichannel_agent(state: GraphState) -> GraphState:
    client = get_llama_client()
    mode = state.get("mode")
    context_lines = []
    for item in state.get("context", []):
        context_lines.append(
            "{source} -[{rel}]-> {target} | source_props={sp} target_props={tp}".format(
                source=item.get("source"),
                rel=item.get("relationship"),
                target=item.get("target"),
                sp=item.get("source_properties"),
                tp=item.get("target_properties"),
            )
        )
    context_text = "\n".join(context_lines)
    messages = [
        {
            "role": "system",
            "content": "You are Omnichannel agent interfacing with end users."
            "Use graph context when available.",
        },
        {
            "role": "user",
            "content": (
                "Mode: {mode}\nIntent: {intent}\nQuery: {query}\nContext:\n{context}"
            ).format(
                mode=mode,
                intent=state.get("intent"),
                query=state.get("query"),
                context=context_text,
            ),
        },
    ]
    reply = client.generate(messages, max_tokens=512)
    state["response"] = reply
    return state
