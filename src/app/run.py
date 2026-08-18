"""Production API entry: ingest catalog if needed, then serve on $PORT.

Railway injects PORT and health-checks 0.0.0.0:$PORT. Local default is 8000.

Public domains are often pinned to 8000 while PORT is 8080 (or the reverse).
That mismatch makes Railway's edge return 502 "Application failed to respond"
with x-railway-fallback=true even when /health passes internally. We TCP-alias
8000 and 8080 to whatever PORT we actually bind.
"""

from __future__ import annotations

import os
import shutil
import socket
import sys
import threading
from pathlib import Path
from typing import Mapping, MutableMapping, Optional, Sequence

RAILWAY_VOLUME_CACHE = Path("/data/processed")
VOLUME_PARQUET_NAME = "restaurants.parquet"
METADATA_NAME = "metadata.json"
DEFAULT_PORT = 8000
REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_PORT_ALIASES = (8000, 8080)


def listen_port(env: Optional[Mapping[str, str]] = None) -> int:
    raw = (env if env is not None else os.environ).get("PORT", str(DEFAULT_PORT))
    try:
        port = int(raw)
    except (TypeError, ValueError) as exc:
        raise SystemExit("PORT must be an integer (Railway injects it). Got: {0!r}".format(raw)) from exc
    if not 1 <= port <= 65535:
        raise SystemExit("PORT out of range: {0}".format(port))
    return port


def extra_public_ports(main_port: int, aliases: Sequence[int] = PUBLIC_PORT_ALIASES) -> list[int]:
    return [port for port in aliases if port != main_port]


def _pipe_sockets(left: socket.socket, right: socket.socket) -> None:
    try:
        while True:
            chunk = left.recv(65536)
            if not chunk:
                break
            right.sendall(chunk)
    except OSError:
        pass
    finally:
        for sock in (left, right):
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass


def start_port_alias(listen: int, dest: int) -> None:
    """Accept TCP on `listen` and splice to 127.0.0.1:`dest` (Railway target-port mismatch)."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", listen))
    server.listen(128)
    server.settimeout(1.0)

    def serve() -> None:
        while True:
            try:
                client, _addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                upstream.connect(("127.0.0.1", dest))
            except OSError:
                client.close()
                continue
            threading.Thread(target=_pipe_sockets, args=(client, upstream), daemon=True).start()
            threading.Thread(target=_pipe_sockets, args=(upstream, client), daemon=True).start()

    threading.Thread(target=serve, daemon=True, name="port-alias-{0}".format(listen)).start()


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
    for extra in extra_public_ports(port):
        try:
            start_port_alias(extra, port)
            print("port-alias: 0.0.0.0:{0} -> {1}".format(extra, port), flush=True)
        except OSError as exc:
            print("port-alias: skip {0}: {1}".format(extra, exc), flush=True)

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
