"""Production entrypoint helpers (Railway $PORT and catalog volume)."""

from __future__ import annotations

import pytest

from src.app.run import apply_volume_defaults, listen_port


def test_listen_port_defaults_to_8000():
    assert listen_port({}) == 8000


def test_listen_port_reads_railway_port():
    assert listen_port({"PORT": "8080"}) == 8080


def test_listen_port_rejects_non_integer():
    with pytest.raises(SystemExit, match="PORT must be an integer"):
        listen_port({"PORT": "$PORT"})


def test_listen_port_rejects_out_of_range():
    with pytest.raises(SystemExit, match="out of range"):
        listen_port({"PORT": "0"})


def test_volume_default_used_when_mount_exists(tmp_path):
    env: dict[str, str] = {}
    apply_volume_defaults(env, volume_dir=tmp_path)
    assert env["DATA_CACHE_DIR"] == str(tmp_path)


def test_volume_default_skips_when_env_set(tmp_path):
    env = {"DATA_CACHE_DIR": "/custom/cache"}
    apply_volume_defaults(env, volume_dir=tmp_path)
    assert env["DATA_CACHE_DIR"] == "/custom/cache"


def test_volume_default_skips_when_mount_missing(tmp_path):
    env: dict[str, str] = {}
    apply_volume_defaults(env, volume_dir=tmp_path / "nope")
    assert "DATA_CACHE_DIR" not in env
