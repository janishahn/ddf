import json
from pathlib import Path
from typing import Optional, Dict, Any
from models import CacheData, Album


class CacheManager:
    """Manages disk and in-memory caching for albums, artist ID, buckets, and track lengths"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache
        self._cache_data: Optional[CacheData] = None
        
        # File paths
        self.artist_id_file = self.cache_dir / "artist_id.json"
        self.albums_file = self.cache_dir / "albums.json"
        self.buckets_file = self.cache_dir / "buckets.json"
        self.lengths_file = self.cache_dir / "lengths.json"
        self.analytics_file = self.cache_dir / "analytics.json"
        
    def load_cache(self) -> CacheData:
        """Load cache data from disk, with fallback to empty cache if files don't exist"""
        if self._cache_data is not None:
            return self._cache_data
            
        # Create empty cache data
        self._cache_data = CacheData()
        
        # Load artist ID
        if self.artist_id_file.exists():
            with open(self.artist_id_file, 'r') as f:
                data = json.load(f)
                self._cache_data.artist_id = data.get('artist_id')
        
        # Load albums
        if self.albums_file.exists():
            with open(self.albums_file, 'r') as f:
                albums_data = json.load(f)
                self._cache_data.albums = [Album(**album) for album in albums_data]
        
        # Load buckets
        if self.buckets_file.exists():
            with open(self.buckets_file, 'r') as f:
                self._cache_data.buckets = json.load(f)
        
        # Load lengths
        if self.lengths_file.exists():
            with open(self.lengths_file, 'r') as f:
                self._cache_data.lengths = json.load(f)
        
        return self._cache_data
    
    def save_cache(self):
        """Save all cache data to disk"""
        if self._cache_data is None:
            return
            
        # Save artist ID
        if self._cache_data.artist_id is not None:
            with open(self.artist_id_file, 'w') as f:
                json.dump({'artist_id': self._cache_data.artist_id}, f)
        
        # Save albums
        albums_data = [album.model_dump() for album in self._cache_data.albums]
        with open(self.albums_file, 'w') as f:
            json.dump(albums_data, f)
        
        # Save buckets
        with open(self.buckets_file, 'w') as f:
            json.dump(self._cache_data.buckets, f)
        
        # Save lengths
        with open(self.lengths_file, 'w') as f:
            json.dump(self._cache_data.lengths, f)
    
    def get_albums(self) -> list[Album]:
        """Get all albums from cache"""
        return self.load_cache().albums
    
    def get_album_by_id(self, collection_id: int) -> Optional[Album]:
        """Get a specific album by collection_id"""
        for album in self.get_albums():
            if album.collection_id == collection_id:
                return album
        return None
    
    def set_albums(self, albums: list[Album]):
        """Set albums in cache"""
        cache = self.load_cache()
        cache.albums = albums
        self.save_cache()
    
    def get_buckets(self) -> dict:
        """Get precomputed buckets"""
        return self.load_cache().buckets
    
    def set_buckets(self, buckets: dict):
        """Set buckets in cache"""
        cache = self.load_cache()
        cache.buckets = buckets
        self.save_cache()
    
    def get_artist_id(self) -> Optional[int]:
        """Get artist ID from cache"""
        cache = self.load_cache()
        return cache.artist_id
    
    def set_artist_id(self, artist_id: int):
        """Set artist ID in cache"""
        cache = self.load_cache()
        cache.artist_id = artist_id
        self.save_cache()
    
    def get_runtime(self, collection_id: int) -> Optional[int]:
        """Get runtime for an album from cache"""
        cache = self.load_cache()
        return cache.lengths.get(str(collection_id))
    
    def set_runtime(self, collection_id: int, runtime_millis: int):
        """Set runtime for an album in cache"""
        cache = self.load_cache()
        cache.lengths[str(collection_id)] = runtime_millis
        self.save_cache()