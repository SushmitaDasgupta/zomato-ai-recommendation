"""Settings helpers used in production (CORS list for Phase 2 Vercel origin)."""

from src.config import Settings


def test_cors_origin_list_default_is_local_next():
    settings = Settings(cors_origins="http://localhost:3000,http://127.0.0.1:3000")
    assert settings.cors_origin_list() == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_cors_origin_list_strips_trailing_slashes_and_blanks():
    settings = Settings(
        cors_origins="https://tablepick.vercel.app/, http://localhost:3000, ,https://tablepick.vercel.app/"
    )
    assert settings.cors_origin_list() == [
        "https://tablepick.vercel.app",
        "http://localhost:3000",
    ]
