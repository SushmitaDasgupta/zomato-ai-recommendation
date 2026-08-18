"""OpenAI-compatible chat client (Groq default) with timeout and one retry."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Mapping, Optional, Protocol, Sequence

import httpx

from src.config import Settings, get_settings
from src.llm.exceptions import LLMError, LLMTimeoutError

logger = logging.getLogger(__name__)


class LLMClient(Protocol):
    def complete(self, messages: Sequence[Mapping[str, str]], *, json_mode: bool = True) -> str:
        """Return the assistant message text."""


class OpenAICompatibleClient:
    """Chat Completions client for Groq (and other OpenAI-compatible providers)."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float = 0.3,
        timeout_seconds: int = 25,
        max_retries: int = 1,
        max_output_tokens: int = 1200,
        transport: Optional[httpx.BaseTransport] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_output_tokens = max_output_tokens
        self.transport = transport

    def complete(self, messages: Sequence[Mapping[str, str]], *, json_mode: bool = True) -> str:
        url = "{0}/chat/completions".format(self.base_url)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [dict(item) for item in messages],
            "temperature": max(1e-8, float(self.temperature)),
            "max_tokens": self.max_output_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": "Bearer {0}".format(self.api_key),
            "Content-Type": "application/json",
        }
        timeout = httpx.Timeout(self.timeout_seconds, connect=5.0)
        last_error: Optional[Exception] = None
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=timeout, transport=self.transport) as client:
                    response = client.post(url, headers=headers, json=payload)
                if response.status_code in {429, 500, 502, 503} and attempt < attempts - 1:
                    logger.warning(
                        "LLM HTTP %s from %s; retrying (%s/%s)",
                        response.status_code,
                        self.base_url,
                        attempt + 1,
                        attempts,
                    )
                    time.sleep(0.4 * (attempt + 1))
                    continue
                if response.status_code >= 400:
                    raise LLMError(
                        "LLM HTTP {0}: {1}".format(response.status_code, _safe_error_body(response))
                    )
                data = response.json()
                text = _choice_text(data)
                if not text:
                    raise LLMError("LLM returned empty content")
                return text
            except LLMError:
                raise
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt >= attempts - 1:
                    raise LLMTimeoutError("LLM request timed out") from exc
                logger.warning("LLM timeout; retrying (%s/%s)", attempt + 1, attempts)
                time.sleep(0.4 * (attempt + 1))
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= attempts - 1:
                    raise LLMError("LLM request failed") from exc
                logger.warning("LLM network error; retrying (%s/%s)", attempt + 1, attempts)
                time.sleep(0.4 * (attempt + 1))
        raise LLMError("LLM request failed") from last_error


def _choice_text(data: Mapping[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for chunk in content:
            if isinstance(chunk, dict) and chunk.get("type") in {"text", "output_text"}:
                parts.append(str(chunk.get("text") or ""))
            elif isinstance(chunk, str):
                parts.append(chunk)
        return "".join(parts).strip()
    return ""


def _safe_error_body(response: httpx.Response) -> str:
    text = (response.text or "").strip().replace("\n", " ")
    return text[:180]


def build_llm_client(settings: Optional[Settings] = None) -> Optional[OpenAICompatibleClient]:
    settings = settings or get_settings()
    api_key = settings.resolved_llm_api_key()
    if not api_key:
        logger.warning(
            "No Groq/LLM API key set; using rule-based fallback. "
            "Add GROQ_API_KEY to .env (console.groq.com)."
        )
        return None
    return OpenAICompatibleClient(
        api_key=api_key,
        base_url=settings.resolved_llm_base_url(),
        model=settings.resolved_llm_model(),
        temperature=settings.llm_temperature,
        timeout_seconds=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
        max_output_tokens=settings.llm_max_output_tokens,
    )
