from datetime import date
from typing import List, Dict
import asyncio
import re

from models import Album
from itunes_client import iTunesClient
from cache import CacheManager


CATALOG_VERSION = 4
DEFAULT_MAX_EPISODE = 240
MAX_EPISODE_SCAN_STEP = 10
MAX_EMPTY_EPISODE_RANGES = 3
MAX_EPISODE_SCAN_EXTENSION = 60
SEARCH_CONCURRENCY = 1
SEARCH_PAUSE_SECONDS = 0.25


class CatalogBuilder:
    """Builds and manages the Die drei ??? album catalog"""

    def __init__(self, cache_manager: CacheManager, itunes_client: iTunesClient):
        self.cache_manager = cache_manager
        self.itunes_client = itunes_client

    async def build_catalog(self, force_refresh: bool = False) -> List[Album]:
        """Build the complete album catalog, using cache if available"""
        today = date.today().isoformat()
        meta = self.cache_manager.get_catalog_meta()
        cached_albums = self.cache_manager.get_albums()

        if not force_refresh:
            if (
                cached_albums
                and meta
                and meta["date"] == today
                and meta["version"] == CATALOG_VERSION
            ):
                await self._precompute_buckets(cached_albums)
                return cached_albums

        max_seed = DEFAULT_MAX_EPISODE
        if meta:
            max_seed = max(max_seed, meta["max_episode"])

        albums_by_number = await self._fetch_episode_range(1, max_seed)
        max_found = max(albums_by_number, default=0)
        scan_start = max_seed + 1
        max_scan_end = max_seed + MAX_EPISODE_SCAN_EXTENSION
        empty_ranges = 0

        while scan_start <= max_scan_end and empty_ranges < MAX_EMPTY_EPISODE_RANGES:
            scan_end = min(
                scan_start + MAX_EPISODE_SCAN_STEP - 1,
                max_scan_end,
            )
            extra = await self._fetch_episode_range(scan_start, scan_end)
            if not extra:
                empty_ranges += 1
                scan_start = scan_end + 1
                continue
            albums_by_number.update(extra)
            max_found = max(max_found, max(extra))
            scan_start = scan_end + 1
            empty_ranges = 0

        if not albums_by_number:
            if cached_albums:
                self.cache_manager.set_catalog_meta(today, max_seed, CATALOG_VERSION)
                await self._precompute_buckets(cached_albums)
                return cached_albums
            return []

        albums = [albums_by_number[number] for number in sorted(albums_by_number)]
        sorted_albums = self._numeric_sort_albums(albums)

        self.cache_manager.set_albums(sorted_albums)
        self.cache_manager.set_catalog_meta(today, max_found, CATALOG_VERSION)

        await self._precompute_buckets(sorted_albums)
        return sorted_albums

    def _numeric_sort_albums(self, albums: List[Album]) -> List[Album]:
        """Sort albums by numeric-aware sorting on collectionName (e.g. 'Folge 2' before 'Folge 10')"""

        def extract_number(text: str) -> tuple:
            match = re.search(r"\d+", text)
            if match:
                number = int(match.group())
                prefix = text[: match.start()]
                suffix = text[match.end() :]
                return (prefix, number, suffix)
            return (text, 0, "")

        return sorted(
            albums, key=lambda album: extract_number(album.collection_name.lower())
        )

    async def _fetch_episode_range(self, start: int, end: int) -> Dict[int, Album]:
        if end < start:
            return {}

        albums_by_number: Dict[int, Album] = {}
        semaphore = asyncio.Semaphore(SEARCH_CONCURRENCY)

        async def fetch_episode(number: int):
            term = f"Folge {number} Die drei ???"
            async with semaphore:
                data = await self.itunes_client.search_albums(term)
                await asyncio.sleep(SEARCH_PAUSE_SECONDS)

            if not data:
                return

            pattern = re.compile(rf"Folge\s+{number}\b", re.IGNORECASE)
            candidates = []
            for result in data.get("results", []):
                if result.get("wrapperType") != "collection":
                    continue
                if result.get("collectionType") != "Album":
                    continue
                if result.get("artistName") != "Die drei ???":
                    continue
                name = result.get("collectionName", "")
                if not pattern.search(name):
                    continue
                candidates.append(result)

            if not candidates:
                return

            candidates.sort(
                key=lambda item: (
                    -(item.get("trackCount") or 0),
                    0 if item.get("collectionPrice") is None else 1,
                )
            )

            album = self.itunes_client.normalize_album_data(candidates[0])
            if album:
                albums_by_number[number] = album

        await asyncio.gather(*(fetch_episode(n) for n in range(start, end + 1)))
        return albums_by_number

    async def _precompute_buckets(self, albums: List[Album]):
        """Precompute age-based buckets: old, medium, new, all"""
        buckets = {
            "all": [album.collection_id for album in albums],
        }

        chronological_albums = sorted(albums, key=self._release_sort_key)

        n = len(chronological_albums)
        if n > 0:
            third_size = n // 3
            remainder = n % 3

            old_end = third_size + (1 if remainder > 0 else 0)
            medium_end = old_end + third_size + (1 if remainder > 1 else 0)

            old_albums = chronological_albums[:old_end]
            medium_albums = chronological_albums[old_end:medium_end]
            new_albums = chronological_albums[medium_end:]

            buckets["old"] = [album.collection_id for album in old_albums]
            buckets["medium"] = [album.collection_id for album in medium_albums]
            buckets["new"] = [album.collection_id for album in new_albums]
        else:
            buckets["old"] = []
            buckets["medium"] = []
            buckets["new"] = []

        self.cache_manager.set_buckets(buckets)

    def _release_sort_key(self, album: Album) -> str:
        """Sort key that prefers precise release dates, then year, defaults newest last"""
        if album.release_date:
            return album.release_date
        if album.year:
            return f"{album.year:04d}-12-31T23:59:59Z"
        return "9999-12-31T23:59:59Z"

    def get_buckets(self) -> Dict[str, List[int]]:
        """Get precomputed buckets"""
        return self.cache_manager.get_buckets()

    def get_album_by_id(self, collection_id: int) -> Album:
        """Get album by collection ID"""
        return self.cache_manager.get_album_by_id(collection_id)

    async def calculate_album_runtime(self, collection_id: int) -> int:
        """Calculate and cache the total runtime of an album in milliseconds"""
        cached_runtime = self.cache_manager.get_runtime(collection_id)
        if cached_runtime is not None:
            return cached_runtime

        track_data = await self.itunes_client.get_tracks_by_album_id(collection_id)
        total_runtime = 0

        if track_data:
            for result in track_data.get("results", []):
                if result.get("wrapperType") == "track":
                    track_time = result.get("trackTimeMillis", 0)
                    total_runtime += track_time

        if total_runtime > 0:
            self.cache_manager.set_runtime(collection_id, total_runtime)

        return total_runtime if total_runtime > 0 else 0
