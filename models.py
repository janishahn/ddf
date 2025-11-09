from pydantic import BaseModel
from typing import Optional, List


class Album(BaseModel):
    """Model for a Die drei ??? album"""
    collection_id: int
    collection_name: str
    artwork_url: str
    release_date: str
    apple_music_url: str
    year: int
    runtime_millis: Optional[int] = None  # Total runtime in milliseconds


class CatalogResponse(BaseModel):
    """Response model for the full album catalog"""
    albums: List[Album]
    total_count: int


class BucketResponse(BaseModel):
    """Response model for a random album from a specific bucket"""
    album: Album
    age: str  # 'old', 'medium', 'new', 'all'


class CacheData(BaseModel):
    """Model for cached data structure"""
    artist_id: Optional[int] = None
    albums: List[Album] = []
    buckets: dict = {}  # Maps 'old', 'medium', 'new', 'all' to lists of collection_ids
    lengths: dict = {}  # Maps collection_id to total runtime in millis