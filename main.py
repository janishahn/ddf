from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
import asyncio
import json
import logging
import random
from typing import Optional

from models import Album
from cache import CacheManager
from itunes_client import iTunesClient
from catalog import CatalogBuilder
from analytics import AnalyticsTracker
from cookies import get_age_cookie, set_age_cookie, validate_age_param


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Die drei ??? Album Viewer")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize components
cache_manager = CacheManager()
itunes_client = iTunesClient()
catalog_builder = CatalogBuilder(cache_manager, itunes_client)
analytics_tracker = AnalyticsTracker(cache_manager)
random_bags: dict[str, list[int]] = {}
random_bag_sources: dict[str, tuple[int, ...]] = {}
refresh_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize the catalog on startup"""
    try:
        await catalog_builder.build_catalog(force_refresh=False)
    except (json.JSONDecodeError, OSError, ValidationError):
        logger.exception("Catalog build failed on startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Save analytics on shutdown"""
    analytics_tracker.save_analytics()
    await itunes_client.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main page with a random album"""
    # Get user's preferred age from cookie or default to "all"
    preferred_age = get_age_cookie(request) or "all"

    # Get a random album from the preferred bucket
    album = await get_random_album_from_bucket(preferred_age)

    if not album:
        # If no albums found, return error page
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "album": None, "error": "No albums found"},
        )

    analytics_tracker.increment_album_shown(album.collection_id)

    runtime_str = None
    if album.runtime_millis:
        minutes = album.runtime_millis // 60000
        seconds = (album.runtime_millis % 60000) // 1000
        runtime_str = f"{minutes}:{seconds:02d}"

    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "album": album,
            "runtime_str": runtime_str,
            "selected_age": preferred_age,
            "error": None,
        },
    )
    set_age_cookie(response, preferred_age)
    return response


@app.get("/random", response_class=HTMLResponse)
async def get_random_album(request: Request, age: str = "all"):
    """Return HTML fragment with a random album for the given age bucket"""
    validated_age = validate_age_param(age)

    album = await get_random_album_from_bucket(validated_age)

    if not album:
        return HTMLResponse(
            content="<div class='text-center p-8 text-gray-500'>No albums available</div>"
        )

    runtime_str = None
    if album.runtime_millis:
        minutes = album.runtime_millis // 60000
        seconds = (album.runtime_millis % 60000) // 1000
        runtime_str = f"{minutes}:{seconds:02d}"

    response = templates.TemplateResponse(
        "_album_fragment.html",
        {
            "request": request,
            "album": album,
            "runtime_str": runtime_str,
            "selected_age": validated_age,
        },
    )
    set_age_cookie(response, validated_age)
    response.headers["Cache-Control"] = "no-store"
    analytics_tracker.increment_and_save_sometimes(validated_age, album.collection_id)
    return response


@app.post("/select-age", response_class=HTMLResponse)
async def select_age(request: Request, age: str = "all"):
    """Update age selection and return new album (alternative to GET /random)"""
    validated_age = validate_age_param(age)

    album = await get_random_album_from_bucket(validated_age)

    if not album:
        return HTMLResponse(
            content="<div class='text-center p-8 text-gray-500'>No albums available</div>"
        )

    runtime_str = None
    if album.runtime_millis:
        minutes = album.runtime_millis // 60000
        seconds = (album.runtime_millis % 60000) // 1000
        runtime_str = f"{minutes}:{seconds:02d}"

    response = templates.TemplateResponse(
        "_album_fragment.html",
        {
            "request": request,
            "album": album,
            "runtime_str": runtime_str,
            "selected_age": validated_age,
        },
    )
    set_age_cookie(response, validated_age)
    response.headers["Cache-Control"] = "no-store"
    analytics_tracker.increment_and_save_sometimes(validated_age, album.collection_id)
    return response


@app.get("/healthz")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


@app.get("/stats")
async def get_stats():
    """Return analytics stats (for admin/development purposes)"""
    return analytics_tracker.get_analytics()


@app.post("/admin/refresh", response_class=HTMLResponse)
async def admin_refresh():
    """Force-refresh the catalog and report the current count"""
    global refresh_task
    if refresh_task and not refresh_task.done():
        response = HTMLResponse(
            "<span class='text-amber-600'>Refresh already running.</span>"
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    refresh_task = asyncio.create_task(
        catalog_builder.build_catalog(force_refresh=True)
    )

    def _on_refresh_done(task: asyncio.Task) -> None:
        global refresh_task
        if task.cancelled():
            if refresh_task is task:
                refresh_task = None
            return
        exc = task.exception()
        if exc:
            logger.error(
                "Catalog refresh failed",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        if refresh_task is task:
            refresh_task = None

    refresh_task.add_done_callback(_on_refresh_done)
    response = HTMLResponse(
        "<span class='text-emerald-600'>Refresh started. This can take a few minutes.</span>"
    )
    response.headers["Cache-Control"] = "no-store"
    return response


async def get_random_album_from_bucket(age: str) -> Optional[Album]:
    """Get a random album from the specified age bucket"""
    albums = cache_manager.get_albums()
    if not albums or len(albums) < 4:
        await catalog_builder.build_catalog(force_refresh=True)

    buckets = catalog_builder.get_buckets()
    if not buckets or not buckets.get(age):
        await catalog_builder.build_catalog(force_refresh=True)
        buckets = catalog_builder.get_buckets()

    collection_ids = buckets.get(age, [])

    if not collection_ids:
        return None

    bag_source = tuple(collection_ids)
    bag = random_bags.get(age)
    if bag_source != random_bag_sources.get(age) or not bag:
        bag = list(bag_source)
        random.shuffle(bag)
        random_bags[age] = bag
        random_bag_sources[age] = bag_source

    collection_id = random_bags[age].pop()
    album = catalog_builder.get_album_by_id(collection_id)

    if not album:
        return None

    return album
