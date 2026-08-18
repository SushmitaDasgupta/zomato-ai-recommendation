"""Production API entry: ingest catalog if needed, then serve on $PORT.

Railway injects PORT and health-checks 0.0.0.0:$PORT. Local default is 8000.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Mapping, MutableMapping, Optional

RAILWAY_VOLUME_CACHE = Path("/data/processed")
VOLUME_PARQUET_NAME = "restaurants.parquet"
METADATA_NAME = "metadata.json"
DEFAULT_PORT = 8000
REPO_ROOT = Path(__file__).resolve().parents[2]


def listen_port(env: Optional[Mapping[str, str]] = None) -> int:
    raw = (env if env is not None else os.environ).get("PORT", str(DEFAULT_PORT))
    try:
        port = int(raw)
    except (TypeError, ValueError) as exc:
        raise SystemExit("PORT must be an integer (Railway injects it). Got: {0!r}".format(raw)) from exc
    if not 1 <= port <= 65535:
        raise SystemExit("PORT out of range: {0}".format(port))
    return port


def apply_volume_defaults(
    env: Optional[MutableMapping[str, str]] = None,
    volume_dir: Path = RAILWAY_VOLUME_CACHE,
) -> None:
    """Use a Railway Volume only when it already has a catalog parquet.

    An empty mount at `/data/processed` must not hide the image's baked cache
    or the API never binds `$PORT` in time for `/health`.
    """
    target = env if env is not None else os.environ
    if str(target.get("DATA_CACHE_DIR", "")).strip():
        return
    if (volume_dir / VOLUME_PARQUET_NAME).is_file():
        target["DATA_CACHE_DIR"] = str(volume_dir)


def seed_baked_catalog(
    env: Optional[Mapping[str, str]] = None,
    repo_root: Path = REPO_ROOT,
) -> None:
    """Copy the image catalog onto DATA_CACHE_DIR when that path is empty.

    Lets a Railway Volume stay empty on first boot without a Hugging Face ingest.
    """
    target = env if env is not None else os.environ
    baked_dir = repo_root / "data" / "processed"
    baked = baked_dir / VOLUME_PARQUET_NAME
    if not baked.is_file():
        return
    cache_raw = str(target.get("DATA_CACHE_DIR", "")).strip()
    cache_dir = Path(cache_raw) if cache_raw else baked_dir
    if not cache_dir.is_absolute():
        cache_dir = (repo_root / cache_dir).resolve()
    dest = cache_dir / VOLUME_PARQUET_NAME
    if dest.is_file() or dest.resolve() == baked.resolve():
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(baked, dest)
    baked_meta = baked_dir / METADATA_NAME
    dest_meta = cache_dir / METADATA_NAME
    if baked_meta.is_file() and not dest_meta.is_file():
        shutil.copy2(baked_meta, dest_meta)


def main() -> None:
    apply_volume_defaults()
    seed_baked_catalog()
    port = listen_port()
    print("start-api: python={0} listening 0.0.0.0:{1} DATA_CACHE_DIR={2}".format(
        sys.executable,
        port,
        os.environ.get("DATA_CACHE_DIR", "(default)"),
    ), flush=True)

    # Bind $PORT before any Hugging Face ingest. A blocked start makes Railway
    # return HTTP 502 "Application failed to respond".
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        timeout_keep_alive=75,
    )


if __name__ == "__main__":
    main()
