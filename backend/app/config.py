from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    llama_api_url: str = Field(
        default="https://redhataillama-31-8b-instruct-model-service.apps.truist-test.sandbox403.opentlc.com/v1/chat/completions"
    )
    llama_model: str = Field(default="redhataillama-31-8b-instruct")
    neo4j_uri: str = Field(
        default="bolt://aadd3663d6966433cb14c2949e347874-822615571.us-east-1.elb.amazonaws.com:7687",
        description="Neo4j Bolt URI; override for local or remote Neo4j instances.",
    )
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="Neo4jStrongPassword123")
    neo4j_database: str = Field(default="neo4j")
    wikipedia_lang: str = Field(default="en")

    class Config:
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(**{**os.environ})
