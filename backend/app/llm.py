from __future__ import annotations

import httpx
from typing import List, Dict

from .config import get_settings


class Llama3Client:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_url = settings.llama_api_url
        self._model = settings.llama_model
        self._client = httpx.Client(timeout=60, verify=False)

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.2,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        response = self._client.post(self._api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")


_llama_client: Llama3Client | None = None


def get_llama_client() -> Llama3Client:
    global _llama_client
    if _llama_client is None:
        _llama_client = Llama3Client()
    return _llama_client
