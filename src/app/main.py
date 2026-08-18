"""FastAPI application: health, filter metadata, hybrid recommendations."""

from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.schemas.meta import BudgetBounds, FilterMetaResponse
from src.app.schemas.recommend import RecommendRequest, RecommendResponse
from src.config import get_settings
from src.data.catalog import Catalog
from src.engine.recommend import recommend
from src.llm.client import LLMClient
from src.observability import configure_logging, get_request_id, metrics, set_request_id
from src.preferences.normalize import PREF_HINTS

logger = logging.getLogger(__name__)


def create_app(
    catalog: Optional[Catalog] = None,
    llm_client: Optional[LLMClient] = None,
    *,
    load_catalog: bool = True,
) -> FastAPI:
    if catalog is not None:
        load_catalog = False

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        if not hasattr(app.state, "catalog"):
            app.state.catalog = None
            if load_catalog:
                def warm() -> None:
                    try:
                        loaded_catalog = Catalog.load()
                        app.state.catalog = loaded_catalog
                        logger.info("Catalog warmed rows=%s", len(loaded_catalog.frame))
                    except Exception:
                        logger.exception(
                            "Catalog failed to load; /health stays up so Railway can bind $PORT"
                        )

                threading.Thread(target=warm, daemon=True, name="catalog-warm").start()
        loaded = getattr(app.state, "catalog", None)
        if loaded is None and not load_catalog:
            logger.warning("API started without a processed catalog. Run: python -m src.data.ingest")
        yield

    app = FastAPI(
        title="Zomato AI Recommendation",
        version="0.4.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if catalog is not None:
        app.state.catalog = catalog
    if llm_client is not None:
        app.state.llm_client = llm_client

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        rid = set_request_id(request.headers.get("x-request-id"))
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"detail": exc.errors()})

    def require_catalog() -> Catalog:
        loaded = getattr(app.state, "catalog", None)
        if loaded is None:
            raise HTTPException(
                status_code=503,
                detail="Processed catalog not found. Run: python -m src.data.ingest",
            )
        return loaded

    @app.get("/")
    def root():
        loaded = getattr(app.state, "catalog", None)
        return {
            "service": "zomato-ai-recommendation",
            "health": "/health",
            "status": "ok" if loaded is not None else "degraded",
        }

    @app.get("/health")
    def health():
        settings = get_settings()
        llm_info = {
            "provider": settings.llm_provider,
            "model": settings.resolved_llm_model(),
            "configured": settings.llm_configured(),
        }
        loaded = getattr(app.state, "catalog", None)
        snapshot = metrics.snapshot()
        if loaded is None:
            return {
                "status": "degraded",
                "catalog_rows": None,
                "detail": "Catalog not loaded. Run python -m src.data.ingest",
                "llm": llm_info,
                "metrics": snapshot,
            }
        return {
            "status": "ok",
            "catalog_rows": int(len(loaded.frame)),
            "llm": llm_info,
            "metrics": snapshot,
        }

    @app.get("/meta/filters", response_model=FilterMetaResponse)
    def meta_filters():
        catalog_obj = require_catalog()
        settings = get_settings()
        return FilterMetaResponse(
            cities=catalog_obj.list_cities(),
            locations=catalog_obj.facet_locations(),
            cuisines=catalog_obj.facet_cuisines(),
            budget_bands=["low", "medium", "high"],
            budget_bounds=BudgetBounds(
                low_max=settings.budget_low_max,
                medium_max=settings.budget_medium_max,
                unit="INR approximate cost for two",
            ),
            min_rating_default=settings.min_rating_default,
            top_k_default=settings.default_top_k,
            additional_preference_hints=list(PREF_HINTS),
            default_location=catalog_obj.default_location(),
            catalog_rows=int(len(catalog_obj.frame)),
        )

    @app.post("/recommend", response_model=RecommendResponse)
    def post_recommend(body: RecommendRequest):
        catalog_obj = require_catalog()
        client = getattr(app.state, "llm_client", None)
        return recommend(
            body,
            catalog=catalog_obj,
            llm_client=client,
            request_id=get_request_id(),
        )

    return app


app = create_app()
