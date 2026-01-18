from typing import List, Dict, Any, Optional
from models import Album
from itunes_client import iTunesClient
from cache import CacheManager
import asyncio
import re


class CatalogBuilder:
    """Builds and manages the Die drei ??? album catalog"""
    
    def __init__(self, cache_manager: CacheManager, itunes_client: iTunesClient):
        self.cache_manager = cache_manager
        self.itunes_client = itunes_client
    
    async def build_catalog(self, force_refresh: bool = False) -> List[Album]:
        """Build the complete album catalog, using cache if available"""
        if not force_refresh:
            cached_albums = self.cache_manager.get_albums()
            if cached_albums:
                streamable_albums = await self._filter_streamable_albums(cached_albums)
                if len(streamable_albums) != len(cached_albums):
                    self.cache_manager.set_albums(streamable_albums)
                # Buckets may need to be recomputed if logic changed or cache was cleared
                await self._precompute_buckets(streamable_albums)
                return streamable_albums
        
        # Get artist ID
        artist_id = self.cache_manager.get_artist_id()
        if not artist_id:
            artist_id = await self.itunes_client.get_artist_id()
            if artist_id:
                self.cache_manager.set_artist_id(artist_id)
        
        if not artist_id:
            raise Exception("Could not find Die drei ??? artist ID")
        
        # Get albums from iTunes
        albums_data = await self.itunes_client.get_albums_by_artist_id(artist_id)
        albums = []
        
        if albums_data:
            # Process results from lookup
            for result in albums_data.get('results', []):
                if result.get('wrapperType') == 'collection' and result.get('collectionType') == 'Album':
                    normalized_album = self.itunes_client.normalize_album_data(result)
                    if normalized_album:
                        albums.append(normalized_album)
        
        # If we got exactly 200 albums, there might be more - try pagination search
        seen_ids = {album.collection_id for album in albums}
        search_offset: Optional[int] = None
        if len(albums) < 50:
            search_offset = 0
        elif len(albums) == 200:
            search_offset = 200

        while search_offset is not None:
            more_data = await self.itunes_client.search_albums("Die drei ???", offset=search_offset)
            if not more_data or more_data.get('resultCount', 0) == 0:
                break

            new_albums = []
            for result in more_data.get('results', []):
                if result.get('wrapperType') == 'collection' and result.get('collectionType') == 'Album':
                    normalized_album = self.itunes_client.normalize_album_data(result)
                    if normalized_album and normalized_album.collection_id not in seen_ids:
                        new_albums.append(normalized_album)
                        seen_ids.add(normalized_album.collection_id)

            if not new_albums:
                break

            albums.extend(new_albums)

            if more_data.get('resultCount', 0) < 200:
                break

            search_offset += 200
        
        streamable_albums = await self._filter_streamable_albums(albums)

        # Sort albums by numeric-aware sorting on collectionName
        sorted_albums = self._numeric_sort_albums(streamable_albums)
        
        # Cache the albums
        self.cache_manager.set_albums(sorted_albums)
        
        # Precompute buckets
        await self._precompute_buckets(sorted_albums)
        
        return sorted_albums
    
    def _numeric_sort_albums(self, albums: List[Album]) -> List[Album]:
        """Sort albums by numeric-aware sorting on collectionName (e.g. 'Folge 2' before 'Folge 10')"""
        def extract_number(text: str) -> tuple:
            # Find the first number in the string
            match = re.search(r'\d+', text)
            if match:
                number = int(match.group())
                # Return tuple of (prefix before number, number, suffix after number)
                prefix = text[:match.start()]
                suffix = text[match.end():]
                return (prefix, number, suffix)
            else:
                # If no number, sort by string
                return (text, 0, '')
        
        return sorted(albums, key=lambda album: extract_number(album.collection_name.lower()))

    async def _filter_streamable_albums(self, albums: List[Album]) -> List[Album]:
        streamable_cache = self.cache_manager.get_streamable()
        missing_albums = [
            album for album in albums
            if str(album.collection_id) not in streamable_cache
        ]

        if missing_albums:
            semaphore = asyncio.Semaphore(6)

            async def check_album(album: Album):
                async with semaphore:
                    track_data = await self.itunes_client.get_tracks_by_album_id(album.collection_id)

                tracks = []
                if track_data:
                    tracks = [
                        result for result in track_data.get('results', [])
                        if result.get('wrapperType') == 'track'
                    ]

                streamable_cache[str(album.collection_id)] = any(
                    track.get('isStreamable') is True for track in tracks
                )

            await asyncio.gather(*(check_album(album) for album in missing_albums))
            self.cache_manager.set_streamable(streamable_cache)

        return [
            album for album in albums
            if streamable_cache.get(str(album.collection_id))
        ]
    
    async def _precompute_buckets(self, albums: List[Album]):
        """Precompute age-based buckets: old, medium, new, all"""
        buckets = {
            'all': [album.collection_id for album in albums]
        }
        
        # Sort by release date so buckets reflect actual appearance order
        chronological_albums = sorted(albums, key=self._release_sort_key)

        # Split albums into thirds for age buckets
        n = len(chronological_albums)
        if n > 0:
            third_size = n // 3
            remainder = n % 3
            
            # Calculate slice points, distributing remainder
            old_end = third_size + (1 if remainder > 0 else 0)
            medium_end = old_end + third_size + (1 if remainder > 1 else 0)
            
            old_albums = chronological_albums[:old_end]
            medium_albums = chronological_albums[old_end:medium_end]
            new_albums = chronological_albums[medium_end:]
            
            buckets['old'] = [album.collection_id for album in old_albums]
            buckets['medium'] = [album.collection_id for album in medium_albums]
            buckets['new'] = [album.collection_id for album in new_albums]
        else:
            # If no albums, empty lists
            buckets['old'] = []
            buckets['medium'] = []
            buckets['new'] = []
        
        # Cache the buckets
        self.cache_manager.set_buckets(buckets)

    def _release_sort_key(self, album: Album) -> str:
        """Sort key that prefers precise release dates, then year, defaults newest last"""
        if album.release_date:
            return album.release_date
        if album.year:
            return f"{album.year:04d}-12-31T23:59:59Z"
        # Unknown release dates should end up in the 'new' bucket
        return "9999-12-31T23:59:59Z"
    
    def get_buckets(self) -> Dict[str, List[int]]:
        """Get precomputed buckets"""
        return self.cache_manager.get_buckets()
    
    def get_album_by_id(self, collection_id: int) -> Album:
        """Get album by collection ID"""
        return self.cache_manager.get_album_by_id(collection_id)
    
    async def calculate_album_runtime(self, collection_id: int) -> int:
        """Calculate and cache the total runtime of an album in milliseconds"""
        # Check if already cached
        cached_runtime = self.cache_manager.get_runtime(collection_id)
        if cached_runtime is not None:
            return cached_runtime
        
        # Fetch track data from iTunes
        track_data = await self.itunes_client.get_tracks_by_album_id(collection_id)
        total_runtime = 0
        
        if track_data:
            for result in track_data.get('results', []):
                if result.get('wrapperType') == 'track':  # Only count actual tracks
                    track_time = result.get('trackTimeMillis', 0)
                    total_runtime += track_time
        
        # Cache the result
        if total_runtime > 0:
            self.cache_manager.set_runtime(collection_id, total_runtime)
        
        return total_runtime if total_runtime > 0 else 0
