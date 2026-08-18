"""Production API entry: ingest catalog if needed, then serve on $PORT.

Railway injects PORT and health-checks 0.0.0.0:$PORT. Local default is 8000.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, MutableMapping, Optional

RAILWAY_VOLUME_CACHE = Path("/data/processed")
DEFAULT_PORT = 8000


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
    """If a Railway Volume is mounted and DATA_CACHE_DIR is unset, use it.

    Avoids writing the parquet to the ephemeral container disk when
    `/data/processed` already exists.
    """
    target = env if env is not None else os.environ
    if str(target.get("DATA_CACHE_DIR", "")).strip():
        return
    if volume_dir.is_dir():
        target["DATA_CACHE_DIR"] = str(volume_dir)


def main() -> None:
    apply_volume_defaults()
    from src.data.ingest import ingest

    ingest()

    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=listen_port(),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
