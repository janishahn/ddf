import json
from pathlib import Path
from typing import Dict
from threading import Lock
from cache import CacheManager


class AnalyticsTracker:
    """Tracks analytics: total rerolls, rerolls per bucket, and times shown per album"""

    def __init__(
        self, cache_manager: CacheManager, analytics_file: str = "cache/analytics.json"
    ):
        self.cache_manager = cache_manager
        self.analytics_file = Path(analytics_file)
        self.analytics_file.parent.mkdir(exist_ok=True)

        # Initialize counters
        self.total_rerolls = 0
        self.rerolls_per_bucket: Dict[str, int] = {
            "old": 0,
            "medium": 0,
            "new": 0,
            "all": 0,
        }
        self.times_shown_per_album: Dict[int, int] = {}

        # Lock for thread safety
        self._lock = Lock()

        # Load existing analytics if available
        self.load_analytics()

    def load_analytics(self):
        """Load analytics from disk"""
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, "r") as f:
                    data = json.load(f)
                    self.total_rerolls = data.get("total_rerolls", 0)
                    self.rerolls_per_bucket = data.get(
                        "rerolls_per_bucket",
                        {"old": 0, "medium": 0, "new": 0, "all": 0},
                    )
                    self.times_shown_per_album = {
                        int(k): v
                        for k, v in data.get("times_shown_per_album", {}).items()
                    }
            except Exception:
                # If loading fails, start with fresh counters
                pass

    def save_analytics(self):
        """Save analytics to disk"""
        try:
            data = {
                "total_rerolls": self.total_rerolls,
                "rerolls_per_bucket": self.rerolls_per_bucket,
                "times_shown_per_album": self.times_shown_per_album,
            }
            with open(self.analytics_file, "w") as f:
                json.dump(data, f)
        except Exception:
            # If saving fails, just continue - don't break the app
            pass

    def increment_reroll(self, bucket: str = "all"):
        """Increment total rerolls and bucket-specific rerolls"""
        with self._lock:
            self.total_rerolls += 1
            self.rerolls_per_bucket[bucket] = self.rerolls_per_bucket.get(bucket, 0) + 1

    def increment_album_shown(self, collection_id: int):
        """Increment times shown for a specific album"""
        with self._lock:
            self.times_shown_per_album[collection_id] = (
                self.times_shown_per_album.get(collection_id, 0) + 1
            )

    def get_analytics(self) -> Dict:
        """Get all analytics data"""
        return {
            "total_rerolls": self.total_rerolls,
            "rerolls_per_bucket": self.rerolls_per_bucket,
            "times_shown_per_album": self.times_shown_per_album,
        }

    def increment_and_save_sometimes(
        self, bucket: str, collection_id: int, save_every: int = 50
    ):
        """Increment counters and save to disk periodically"""
        with self._lock:
            self.total_rerolls += 1
            self.rerolls_per_bucket[bucket] = self.rerolls_per_bucket.get(bucket, 0) + 1
            self.times_shown_per_album[collection_id] = (
                self.times_shown_per_album.get(collection_id, 0) + 1
            )

            if self.total_rerolls % save_every == 0:
                self.save_analytics()
