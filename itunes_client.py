import asyncio
from typing import Optional, Dict, Any

import httpx

from models import Album


class iTunesClient:
    """Client for interacting with iTunes/Apple Music API"""

    def __init__(self, timeout: int = 10, retries: int = 3):
        self.base_url = "https://itunes.apple.com"
        self.country = "DE"  # German storefront
        self.timeout = timeout
        self.retries = retries
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def search_albums(self, term: str) -> Optional[Dict[str, Any]]:
        """Search for albums by term"""
        url = f"{self.base_url}/search"
        params = {
            "term": term,
            "entity": "album",
            "limit": 200,
            "country": self.country,
        }

        for attempt in range(self.retries):
            try:
                response = await self.client.get(url, params=params)
            except httpx.RequestError:
                if attempt == self.retries - 1:
                    return None
                await asyncio.sleep(2**attempt)
                continue

            if response.status_code == 200:
                return response.json()

            if response.status_code in {403, 429}:
                if attempt == self.retries - 1:
                    return None
                await asyncio.sleep(5 * (attempt + 1))
                continue

            if attempt == self.retries - 1:
                return None

            await asyncio.sleep(2**attempt)

        return None

    async def get_tracks_by_album_id(
        self, collection_id: int, limit: int | None = None
    ) -> Optional[Dict[str, Any]]:
        """Get tracks by album ID"""
        url = f"{self.base_url}/lookup"
        params = {
            "id": collection_id,
            "entity": "song",
            "country": self.country,
        }
        if limit is not None:
            params["limit"] = limit

        # Shorter timeout for runtime fetch
        for attempt in range(2):  # Only 2 retries for runtime
            try:
                response = await self.client.get(url, params=params, timeout=3.0)
            except httpx.TimeoutException:
                return None
            except httpx.RequestError:
                if attempt == 1:
                    return None
                await asyncio.sleep(1**attempt)
                continue

            if response.status_code == 200:
                return response.json()

            if response.status_code in {403, 429}:
                if attempt == 1:
                    return None
                await asyncio.sleep(2 * (attempt + 1))
                continue

            if attempt == 1:
                return None
            await asyncio.sleep(1**attempt)

        return None

    def normalize_album_data(self, raw_album: Dict[str, Any]) -> Optional[Album]:
        """Normalize raw iTunes album data to Album model"""
        # Only include albums that match the expected pattern
        collection_name = raw_album.get("collectionName", "")
        artist_name = raw_album.get("artistName", "")
        normalized_collection = collection_name.lower()
        normalized_artist = artist_name.lower()
        if not (
            "die drei ???" in normalized_collection
            or "die drei fragezeichen" in normalized_collection
            or "die drei ???" in normalized_artist
        ):
            return None

        # Get artwork URL - start with 100x100 and upgrade to higher resolution
        artwork_url = raw_album.get("artworkUrl100", "")
        if artwork_url:
            # Try to upgrade to 1000x1000, fallback to 600x600, then 100x100
            artwork_url = artwork_url.replace("100x100", "1000x1000")

        release_date = raw_album.get("releaseDate", "")
        year = 0
        if release_date:
            try:
                # Parse year from release date (format: "YYYY-MM-DDTHH:MM:SSSZ")
                year = int(release_date[:4])
            except (ValueError, IndexError):
                pass

        return Album(
            collection_id=raw_album.get("collectionId", 0),
            collection_name=collection_name,
            artwork_url=artwork_url,
            release_date=release_date,
            apple_music_url=raw_album.get("collectionViewUrl", ""),
            year=year,
        )
