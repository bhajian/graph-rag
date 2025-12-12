from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ContextChunk(BaseModel):
    source: str
    target: str
    relationship: str
    summary: Optional[str] = None


class IngestPayload(BaseModel):
    text: str = Field(..., description="Raw text to ingest")
    source: str | None = Field(default=None, description="Optional source identifier")


class IngestResponse(BaseModel):
    message: str
    entities: List[str]


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    context: List[ContextChunk] = Field(default_factory=list)
