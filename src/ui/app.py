"""Streamlit preference form and recommendation cards (Phase 3)."""

from __future__ import annotations

import streamlit as st

from src.app.schemas.recommend import RecommendRequest
from src.config import get_settings
from src.data.catalog import Catalog
from src.data.ingest import CatalogCacheError
from src.engine.recommend import recommend
from src.preferences.normalize import PREF_HINTS

PRESETS = {
    "Bangalore · Italian · medium": {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": ["Italian"],
        "min_rating": 4.0,
        "additional": "family-friendly",
        "top_k": 5,
    },
    "Multi-cuisine night out": {
        "location": "Bangalore",
        "budget": "medium",
        "cuisine": ["Italian", "Chinese"],
        "min_rating": 3.5,
        "additional": "casual",
        "top_k": 5,
    },
    "Romantic rooftop": {
        "location": "Bangalore",
        "budget": "high",
        "cuisine": [],
        "min_rating": 4.0,
        "additional": "romantic rooftop",
        "top_k": 5,
    },
    "Impossible filters (empty state)": {
        "location": "Atlantis",
        "budget": "low",
        "cuisine": ["Martian"],
        "min_rating": 4.9,
        "additional": "",
        "top_k": 5,
    },
}


@st.cache_resource
def load_catalog() -> Catalog:
    return Catalog.load()


def _format_cost(value) -> str:
    if value is None:
        return "N/A"
    return "₹{0:.0f} for two".format(value)


def _format_rating(value) -> str:
    if value is None:
        return "N/A"
    return "{0:.1f}".format(value)


def _init_defaults(catalog: Catalog) -> None:
    if "form_location" not in st.session_state:
        st.session_state.form_location = catalog.default_location() or ""
    if "form_budget" not in st.session_state:
        st.session_state.form_budget = "medium"
    if "form_cuisine" not in st.session_state:
        st.session_state.form_cuisine = ["Italian"] if "Italian" in catalog.list_cuisines() else []
    if "form_min_rating" not in st.session_state:
        st.session_state.form_min_rating = 3.5
    if "form_top_k" not in st.session_state:
        st.session_state.form_top_k = 5
    if "form_additional" not in st.session_state:
        st.session_state.form_additional = ""


def _apply_preset(name: str) -> None:
    data = PRESETS[name]
    st.session_state.form_location = data["location"]
    st.session_state.form_budget = data["budget"]
    st.session_state.form_cuisine = list(data["cuisine"])
    st.session_state.form_min_rating = data["min_rating"]
    st.session_state.form_top_k = data["top_k"]
    st.session_state.form_additional = data["additional"]


def main() -> None:
    st.set_page_config(page_title="Zomato AI Recommendations", layout="wide")
    st.title("Restaurant recommendations")
    st.caption(
        "Filter the Zomato catalog, then rank and explain with Groq. "
        "Rule-based ranking is used if the model is unavailable."
    )

    settings = get_settings()
    if not settings.llm_configured():
        st.warning(
            "No Groq API key found. Results will use rule-based ranking. "
            "Copy `.env.example` to `.env` and set `GROQ_API_KEY`."
        )

    try:
        catalog = load_catalog()
    except CatalogCacheError as exc:
        st.error(str(exc))
        st.info("From the project root run: `python -m src.data.ingest`")
        st.stop()

    locations = catalog.facet_locations()
    cuisines = catalog.facet_cuisines()
    st.session_state._location_options = locations
    _init_defaults(catalog)

    use_dropdowns = bool(locations) and bool(cuisines)
    if not use_dropdowns:
        st.info("Catalog facets were empty, so location and cuisine fall back to free text.")

    preset_col, load_col = st.columns([3, 1])
    with preset_col:
        preset = st.selectbox("Demo walkthrough", ["Custom"] + list(PRESETS.keys()))
    with load_col:
        st.write("")
        if st.button("Load preset", disabled=preset == "Custom"):
            _apply_preset(preset)
            st.rerun()

    with st.form("preferences"):
        col1, col2 = st.columns(2)
        with col1:
            if use_dropdowns:
                options = list(locations)
                current = st.session_state.form_location
                if current and current not in options:
                    options = [current] + options
                location = st.selectbox("Location", options, key="form_location")
                custom = st.text_input(
                    "Or type a location",
                    value="",
                    placeholder="Override the dropdown",
                    help="Leave blank to use the dropdown value.",
                )
                if custom.strip():
                    location = custom.strip()
            else:
                location = st.text_input("Location", key="form_location")
            budget = st.selectbox("Budget", ["low", "medium", "high"], key="form_budget")
            if use_dropdowns:
                cuisine_options = list(cuisines)
                for item in st.session_state.get("form_cuisine") or []:
                    if item not in cuisine_options:
                        cuisine_options.append(item)
                cuisine_sel = st.multiselect("Cuisine", cuisine_options, key="form_cuisine")
            else:
                cuisine_raw = st.text_input("Cuisine (comma-separated, optional)", value="Italian")
                cuisine_sel = [part.strip() for part in cuisine_raw.split(",") if part.strip()]
        with col2:
            min_rating = st.slider(
                "Minimum rating",
                min_value=0.0,
                max_value=5.0,
                step=0.1,
                key="form_min_rating",
            )
            top_k = st.slider("How many results", min_value=1, max_value=10, key="form_top_k")
            additional = st.text_area(
                "Additional preferences",
                placeholder="family-friendly, quiet ambience, rooftop",
                key="form_additional",
            )
            st.caption("Hints: " + ", ".join(PREF_HINTS))
        submitted = st.form_submit_button("Get recommendations", type="primary")

    if not submitted:
        st.info("Set your preferences and submit to see ranked restaurants.")
        return

    try:
        request = RecommendRequest(
            location=location,
            budget=budget,
            cuisine=list(cuisine_sel),
            min_rating=min_rating,
            additional_preferences=additional or "",
            top_k=top_k,
        )
    except Exception as exc:  # pydantic validation
        st.error(str(exc))
        return

    with st.status("Finding restaurants…", expanded=True) as status:
        status.write("Applying location, cuisine, rating, and budget filters")
        status.write("Ranking the shortlist and writing explanations")
        result = recommend(request, catalog=catalog)
        status.update(label="Recommendations ready", state="complete")
    meta = result.meta

    if not result.recommendations:
        st.error("No restaurants matched those filters.")
        st.markdown("**Try relaxing:**")
        if meta.suggestions:
            for tip in meta.suggestions:
                st.markdown("- " + tip)
        else:
            st.markdown("- Lower the minimum rating, widen budget, or pick a different location")
        if meta.filter_stage_counts:
            st.caption("Filter counts: " + ", ".join(
                "{0}={1}".format(key, value) for key, value in meta.filter_stage_counts.items()
            ))
        return

    if result.summary:
        st.success(result.summary)

    if meta.source == "llm":
        st.caption(
            "AI ranking via {provider} ({model})".format(
                provider=settings.llm_provider,
                model=meta.llm_model or settings.resolved_llm_model(),
            )
        )
    else:
        reason = meta.fallback_reason or "unavailable"
        st.info(
            "Showing rule-based ranking ({reason}). Structured fields still come from the catalog.".format(
                reason=reason.replace("_", " ")
            )
        )

    if meta.relaxations_applied:
        st.caption("Relaxed constraints: " + ", ".join(meta.relaxations_applied))

    breakdown = meta.latency_breakdown
    latency_bits = "{n} shown · {c} candidates".format(
        n=len(result.recommendations),
        c=meta.candidates_considered,
    )
    if breakdown:
        latency_bits += " · filter {f} ms · LLM {l} ms · total {t} ms".format(
            f=breakdown.filter_ms,
            l=breakdown.llm_ms,
            t=breakdown.total_ms,
        )
    elif meta.latency_ms is not None:
        latency_bits += " · {0} ms".format(meta.latency_ms)
    st.caption(latency_bits)

    for item in result.recommendations:
        with st.container(border=True):
            heading, badge = st.columns([4, 1])
            with heading:
                st.subheader("{rank}. {name}".format(rank=item.rank, name=item.name))
            with badge:
                st.caption("AI" if item.source == "llm" else "Rules")
            st.markdown(
                "**{cuisine}** · Rating {rating} · {cost} · {location}".format(
                    cuisine=item.cuisine,
                    rating=_format_rating(item.rating),
                    cost=_format_cost(item.estimated_cost),
                    location=item.location,
                )
            )
            st.markdown(item.explanation)
            if item.fit_notes:
                st.caption("Fit: " + ", ".join(item.fit_notes))


main()
