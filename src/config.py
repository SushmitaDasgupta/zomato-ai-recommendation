"""Environment-driven settings (architecture §9)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_dataset_id: str = "ManikaSaini/zomato-restaurant-recommendation"
    data_cache_dir: Path = Field(default=PROJECT_ROOT / "data" / "processed")

    # Assumed unit: INR approximate cost for two people (architecture budget table).
    budget_low_max: float = 500
    budget_medium_max: float = 1500

    default_top_k: int = 5
    max_candidates_for_llm: int = 25
    min_candidates: int = 5
    min_rating_default: float = 3.5
    max_additional_preferences_chars: int = 500
    max_explanation_chars: int = 400
    log_level: str = "INFO"
    recommend_cache_ttl_seconds: int = 0
    recommend_cache_maxsize: int = 128
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Groq is the default provider (OpenAI-compatible chat completions).
    llm_provider: str = "groq"
    llm_model: str = "llama-3.1-8b-instant"
    llm_api_key: str = ""
    groq_api_key: str = ""
    llm_base_url: str = ""
    llm_temperature: float = 0.3
    llm_timeout_seconds: int = 25
    llm_max_retries: int = 1
    llm_max_output_tokens: int = 1200

    @field_validator("budget_low_max", "budget_medium_max")
    @classmethod
    def _positive_budget(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("budget thresholds must be positive")
        return value

    @model_validator(mode="after")
    def _validate_bands_and_caps(self) -> "Settings":
        if self.budget_low_max >= self.budget_medium_max:
            raise ValueError("BUDGET_LOW_MAX must be less than BUDGET_MEDIUM_MAX")
        if self.max_candidates_for_llm < 1:
            raise ValueError("MAX_CANDIDATES_FOR_LLM must be at least 1")
        if self.min_candidates < 1:
            raise ValueError("MIN_CANDIDATES must be at least 1")
        if self.recommend_cache_ttl_seconds < 0:
            raise ValueError("RECOMMEND_CACHE_TTL_SECONDS cannot be negative")
        return self

    def resolved_cache_dir(self) -> Path:
        path = self.data_cache_dir
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path.resolve()

    def resolved_llm_api_key(self) -> str:
        if self.llm_provider.strip().casefold() == "groq":
            return (self.groq_api_key or self.llm_api_key).strip()
        return (self.llm_api_key or self.groq_api_key).strip()

    def resolved_llm_base_url(self) -> str:
        if self.llm_base_url.strip():
            return self.llm_base_url.strip().rstrip("/")
        provider = self.llm_provider.strip().casefold()
        if provider == "openai":
            return "https://api.openai.com/v1"
        return "https://api.groq.com/openai/v1"

    def resolved_llm_model(self) -> str:
        if self.llm_model.strip():
            return self.llm_model.strip()
        if self.llm_provider.strip().casefold() == "openai":
            return "gpt-4o-mini"
        return "llama-3.1-8b-instant"

    def llm_configured(self) -> bool:
        return bool(self.resolved_llm_api_key())

    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
