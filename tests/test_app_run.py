"""Production entrypoint helpers (Railway $PORT and catalog volume)."""

from __future__ import annotations

import pytest

from src.app.run import apply_volume_defaults, extra_public_ports, listen_port, seed_baked_catalog


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


def test_extra_public_ports_aliases_8000_and_8080():
    assert extra_public_ports(8080) == [8000]
    assert extra_public_ports(8000) == [8080]
    assert extra_public_ports(3000) == [8000, 8080]


def test_volume_default_used_when_parquet_exists(tmp_path):
    (tmp_path / "restaurants.parquet").write_bytes(b"x")
    env: dict[str, str] = {}
    apply_volume_defaults(env, volume_dir=tmp_path)
    assert env["DATA_CACHE_DIR"] == str(tmp_path)


def test_volume_default_skips_empty_mount(tmp_path):
    env: dict[str, str] = {}
    apply_volume_defaults(env, volume_dir=tmp_path)
    assert "DATA_CACHE_DIR" not in env


def test_volume_default_skips_when_env_set(tmp_path):
    (tmp_path / "restaurants.parquet").write_bytes(b"x")
    env = {"DATA_CACHE_DIR": "/custom/cache"}
    apply_volume_defaults(env, volume_dir=tmp_path)
    assert env["DATA_CACHE_DIR"] == "/custom/cache"


def test_volume_default_skips_when_mount_missing(tmp_path):
    env: dict[str, str] = {}
    apply_volume_defaults(env, volume_dir=tmp_path / "nope")
    assert "DATA_CACHE_DIR" not in env


def test_seed_copies_baked_catalog_into_empty_cache(tmp_path):
    repo = tmp_path / "repo"
    baked = repo / "data" / "processed"
    baked.mkdir(parents=True)
    (baked / "restaurants.parquet").write_bytes(b"catalog")
    (baked / "metadata.json").write_text("{}", encoding="utf-8")
    dest = tmp_path / "volume"
    seed_baked_catalog({"DATA_CACHE_DIR": str(dest)}, repo_root=repo)
    assert (dest / "restaurants.parquet").read_bytes() == b"catalog"
    assert (dest / "metadata.json").read_text(encoding="utf-8") == "{}"


def test_seed_skips_when_cache_already_has_parquet(tmp_path):
    repo = tmp_path / "repo"
    baked = repo / "data" / "processed"
    baked.mkdir(parents=True)
    (baked / "restaurants.parquet").write_bytes(b"new")
    dest = tmp_path / "volume"
    dest.mkdir()
    (dest / "restaurants.parquet").write_bytes(b"old")
    seed_baked_catalog({"DATA_CACHE_DIR": str(dest)}, repo_root=repo)
    assert (dest / "restaurants.parquet").read_bytes() == b"old"
