"""LLM client and parse failures (orchestrator maps these to fallback)."""

from __future__ import annotations


class LLMError(Exception):
    """Base error for provider or parse failures."""


class LLMTimeoutError(LLMError):
    """Provider call exceeded the configured timeout."""


class LLMParseError(LLMError):
    """Model output could not be parsed into the expected JSON schema."""
