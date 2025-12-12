from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import get_settings
from .graph import build_graph
from .schemas import ChatRequest, ChatResponse, ContextChunk, IngestPayload, IngestResponse

load_dotenv()

app = FastAPI(title="LangGraph Neo4j Agents", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _invoke_graph(state):
    graph = build_graph()
    return graph.invoke(state)


@app.get("/health")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "llama_model": settings.llama_model,
        "neo4j_uri": settings.neo4j_uri,
    }


@app.post("/api/ingest", response_model=IngestResponse)
def ingest(payload: IngestPayload):
    final_state = _invoke_graph(
        {
            "mode": "ingest",
            "text": payload.text,
            "query": payload.text,
            "source": payload.source,
            "history": [],
            "intent": "ingest",
        }
    )
    entities = [entity.get("name") for entity in final_state.get("entity_graph", []) if entity.get("name")]
    return IngestResponse(
        message=final_state.get("response", "Ingestion complete."),
        entities=entities,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    final_state = _invoke_graph(
        {
            "mode": "retrieve",
            "query": request.message,
            "history": [turn.dict() for turn in request.history],
        }
    )
    context = [
        ContextChunk(
            source=item.get("source"),
            target=item.get("target"),
            relationship=item.get("relationship"),
            summary=f"{item.get('source_properties')} -> {item.get('target_properties')}",
        )
        for item in final_state.get("context", [])
    ]
    return ChatResponse(reply=final_state.get("response", ""), context=context)
