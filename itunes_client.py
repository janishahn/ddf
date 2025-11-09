import httpx
from typing import Optional, List, Dict, Any
from models import Album
import asyncio


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
    
    async def search_artist(self, term: str) -> Optional[Dict[str, Any]]:
        """Search for an artist by name"""
        url = f"{self.base_url}/search"
        params = {
            "term": term,
            "entity": "musicArtist",
            "limit": 5,
            "country": self.country
        }
        
        for attempt in range(self.retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                if attempt == self.retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def get_albums_by_artist_id(self, artist_id: int) -> Optional[Dict[str, Any]]:
        """Get albums by artist ID (lookup method)"""
        url = f"{self.base_url}/lookup"
        params = {
            "id": artist_id,
            "entity": "album",
            "limit": 200,
            "country": self.country
        }
        
        for attempt in range(self.retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                if attempt == self.retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def search_albums(self, term: str, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Search for albums by term with pagination (fallback if lookup fails)"""
        url = f"{self.base_url}/search"
        params = {
            "term": term,
            "entity": "album",
            "limit": 200,
            "offset": offset,
            "country": self.country
        }
        
        for attempt in range(self.retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                if attempt == self.retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def get_tracks_by_album_id(self, collection_id: int) -> Optional[Dict[str, Any]]:
        """Get tracks by album ID to calculate total runtime"""
        url = f"{self.base_url}/lookup"
        params = {
            "id": collection_id,
            "entity": "song",
            "country": self.country
        }
        
        # Shorter timeout for runtime fetch
        for attempt in range(2):  # Only 2 retries for runtime
            try:
                response = await self.client.get(url, params=params, timeout=3.0)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                # If timeout, return None instead of retrying
                return None
            except httpx.RequestError as e:
                if attempt == 1:
                    return None  # Return None on error for runtime
                await asyncio.sleep(1 ** attempt)
        
        return None
    
    def normalize_album_data(self, raw_album: Dict[str, Any]) -> Optional[Album]:
        """Normalize raw iTunes album data to Album model"""
        # Only include albums that match the expected pattern
        collection_name = raw_album.get('collectionName', '')
        artist_name = raw_album.get('artistName', '')
        normalized_collection = collection_name.lower()
        normalized_artist = artist_name.lower()
        if not (
            'die drei ???' in normalized_collection
            or 'die drei fragezeichen' in normalized_collection
            or 'die drei ???' in normalized_artist
        ):
            return None
            
        # Get artwork URL - start with 100x100 and upgrade to higher resolution
        artwork_url = raw_album.get('artworkUrl100', '')
        if artwork_url:
            # Try to upgrade to 1000x1000, fallback to 600x600, then 100x100
            artwork_url = artwork_url.replace('100x100', '1000x1000')
            
        release_date = raw_album.get('releaseDate', '')
        year = 0
        if release_date:
            try:
                # Parse year from release date (format: "YYYY-MM-DDTHH:MM:SSSZ")
                year = int(release_date[:4])
            except (ValueError, IndexError):
                pass
        
        return Album(
            collection_id=raw_album.get('collectionId', 0),
            collection_name=collection_name,
            artwork_url=artwork_url,
            release_date=release_date,
            apple_music_url=raw_album.get('collectionViewUrl', ''),
            year=year
        )
    
    async def get_artist_id(self, search_term: str = "Die drei ???") -> Optional[int]:
        """Get artist ID by searching for the artist"""
        result = await self.search_artist(search_term)
        if result and result.get('resultCount', 0) > 0:
            return result['results'][0].get('artistId')
        return None