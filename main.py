from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import asyncio
import json
import logging
import random
from pathlib import Path
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

# Initialize components
cache_manager = CacheManager()
itunes_client = iTunesClient()
catalog_builder = CatalogBuilder(cache_manager, itunes_client)
analytics_tracker = AnalyticsTracker(cache_manager)
random_bags: dict[str, list[int]] = {}
random_bag_sources: dict[str, tuple[int, ...]] = {}
refresh_task: asyncio.Task | None = None
startup_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize the catalog on startup"""
    global startup_task

    async def _build_on_startup() -> None:
        try:
            await catalog_builder.build_catalog(force_refresh=False)
        except (json.JSONDecodeError, OSError, ValidationError):
            logger.exception("Catalog build failed on startup")

    startup_task = asyncio.create_task(_build_on_startup())


@app.on_event("shutdown")
async def shutdown_event():
    """Save analytics on shutdown"""
    analytics_tracker.save_analytics()
    await itunes_client.close()


@app.get("/api/healthz")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


@app.get("/api/stats")
async def get_stats():
    """Return analytics stats (for admin/development purposes)"""
    return analytics_tracker.get_analytics()


@app.get("/api/admin/catalog/status")
async def admin_catalog_status():
    """Get catalog refresh status for the SPA"""
    response = JSONResponse(catalog_builder.get_refresh_status())
    response.headers["Cache-Control"] = "no-store"
    return response


@app.post("/api/admin/catalog/refresh")
async def admin_catalog_refresh():
    """Force-refresh the catalog and report the current count"""
    global refresh_task
    if refresh_task and not refresh_task.done():
        response = JSONResponse(
            {"state": "running", "started": False},
            status_code=status.HTTP_202_ACCEPTED,
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
            catalog_builder.mark_refresh_error("exception")
            logger.error(
                "Catalog refresh failed",
                exc_info=(type(exc), exc, exc.__traceback__),
            )
        if refresh_task is task:
            refresh_task = None

    refresh_task.add_done_callback(_on_refresh_done)
    response = JSONResponse(
        {"state": "running", "started": True},
        status_code=status.HTTP_202_ACCEPTED,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/albums/random")
async def api_random_album(
    request: Request, age: Optional[str] = None, reroll: bool = False
):
    """Return a random album from the specified bucket"""
    preferred_age = get_age_cookie(request)
    selected_age = validate_age_param(age) if age else (preferred_age or "all")

    album = await get_random_album_from_bucket(selected_age)
    if not album:
        response = JSONResponse(
            {"error": "no_albums"}, status_code=status.HTTP_404_NOT_FOUND
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    runtime_str = None
    if album.runtime_millis:
        minutes = album.runtime_millis // 60000
        seconds = (album.runtime_millis % 60000) // 1000
        runtime_str = f"{minutes}:{seconds:02d}"

    payload = {
        "age": selected_age,
        "album": album.model_dump(),
        "runtime_millis": album.runtime_millis,
        "runtime_str": runtime_str,
    }

    response = JSONResponse(payload)
    set_age_cookie(response, selected_age)
    response.headers["Cache-Control"] = "no-store"

    if reroll:
        analytics_tracker.increment_and_save_sometimes(
            selected_age, album.collection_id
        )
    else:
        analytics_tracker.increment_album_shown(album.collection_id)
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


def mount_spa() -> None:
    dist_path = Path(__file__).resolve().parent / "frontend" / "dist"
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="spa")


mount_spa()
