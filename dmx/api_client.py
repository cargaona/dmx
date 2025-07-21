"""Production-ready API client for music search and metadata."""

import asyncio
import aiohttp
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 5.0
    burst_size: int = 10
    cooldown_period: float = 1.0


class APIError(Exception):
    """Base API error."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded error."""
    pass


class APIClient:
    """Production-ready API client with rate limiting and caching."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit = RateLimitConfig()
        self.last_request_time = 0.0
        self.request_count = 0
        self.cache_dir = (config_dir or Path.home() / ".config" / "dmx") / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour
        self.max_cache_size = 1000
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'dmx/1.0.0 (Music Search Client)',
                'Accept': 'application/json',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        
        # Reset counter if enough time has passed
        if current_time - self.last_request_time > self.rate_limit.cooldown_period:
            self.request_count = 0
        
        # Check if we're within rate limits
        if self.request_count >= self.rate_limit.burst_size:
            time_to_wait = self.rate_limit.cooldown_period - (current_time - self.last_request_time)
            if time_to_wait > 0:
                logger.info(f"Rate limiting: waiting {time_to_wait:.2f}s")
                await asyncio.sleep(time_to_wait)
                self.request_count = 0
        
        # Implement requests per second limit
        min_interval = 1.0 / self.rate_limit.requests_per_second
        time_since_last = current_time - self.last_request_time
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.request_count += 1
        self.last_request_time = time.time()
    
    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for request."""
        import hashlib
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is still valid."""
        if not cache_file.exists():
            return False
        
        # Check age
        cache_age = time.time() - cache_file.stat().st_mtime
        return cache_age < self.cache_ttl
    
    def _read_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Read from cache."""
        cache_file = self._get_cache_file(cache_key)
        
        if not self._is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to read cache {cache_key}: {e}")
            return None
    
    def _write_cache(self, cache_key: str, data: Dict[str, Any]):
        """Write to cache."""
        cache_file = self._get_cache_file(cache_key)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except OSError as e:
            logger.warning(f"Failed to write cache {cache_key}: {e}")
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and error handling."""
        if not self.session:
            raise APIError("Session not initialized")
        
        await self._rate_limit()
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                
                response.raise_for_status()
                return await response.json()
        
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {e}")
    
    async def search_musicbrainz(self, query: str, entity: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search MusicBrainz for metadata."""
        # MusicBrainz is free and doesn't require API keys
        base_url = "https://musicbrainz.org/ws/2"
        
        params = {
            'query': query,
            'fmt': 'json',
            'limit': min(limit, 100)
        }
        
        cache_key = self._get_cache_key(f"mb_{entity}", params)
        cached_result = self._read_cache(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for MusicBrainz {entity} search: {query}")
            return cached_result.get('results', [])
        
        url = f"{base_url}/{entity}"
        
        try:
            data = await self._make_request('GET', url, params=params)
            results = self._format_musicbrainz_results(data, entity)
            
            # Cache the results
            self._write_cache(cache_key, {'results': results})
            
            return results
        
        except Exception as e:
            logger.error(f"MusicBrainz search failed: {e}")
            return []
    
    def _format_musicbrainz_results(self, data: Dict[str, Any], entity: str) -> List[Dict[str, Any]]:
        """Format MusicBrainz search results."""
        results = []
        items = data.get(entity + 's', [])  # recordings, releases, artists
        
        for item in items:
            if entity == 'recording':
                # Track format
                artist_name = 'Unknown'
                if item.get('artist-credit'):
                    artist_name = item['artist-credit'][0].get('name', 'Unknown')
                
                album_name = 'Unknown'
                if item.get('releases'):
                    album_name = item['releases'][0].get('title', 'Unknown')
                
                results.append({
                    'id': item.get('id'),
                    'title': item.get('title', 'Unknown'),
                    'artist': artist_name,
                    'album': album_name,
                    'duration': self._format_duration(item.get('length', 0)),
                    'type': 'track',
                    'url': f"https://musicbrainz.org/recording/{item.get('id')}",
                    'score': item.get('score', 0)
                })
            
            elif entity == 'release':
                # Album format
                artist_name = 'Unknown'
                if item.get('artist-credit'):
                    artist_name = item['artist-credit'][0].get('name', 'Unknown')
                
                results.append({
                    'id': item.get('id'),
                    'title': item.get('title', 'Unknown'),
                    'artist': artist_name,
                    'tracks': item.get('track-count', 0),
                    'type': 'album',
                    'url': f"https://musicbrainz.org/release/{item.get('id')}",
                    'score': item.get('score', 0)
                })
            
            elif entity == 'artist':
                # Artist format
                results.append({
                    'id': item.get('id'),
                    'name': item.get('name', 'Unknown'),
                    'albums': 0,  # Would need separate query
                    'fans': 0,   # Not available in MusicBrainz
                    'type': 'artist',
                    'url': f"https://musicbrainz.org/artist/{item.get('id')}",
                    'score': item.get('score', 0)
                })
        
        # Sort by score (relevance)
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return results
    
    def _format_duration(self, length_ms: Optional[int]) -> str:
        """Format duration from milliseconds to MM:SS."""
        if not length_ms:
            return "0:00"
        
        seconds = length_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    async def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tracks using MusicBrainz."""
        return await self.search_musicbrainz(query, 'recording', limit)
    
    async def search_albums(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for albums using MusicBrainz."""
        return await self.search_musicbrainz(query, 'release', limit)
    
    async def search_artists(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for artists using MusicBrainz."""
        return await self.search_musicbrainz(query, 'artist', limit)
    
    def cleanup_cache(self):
        """Clean up old cache files."""
        if not self.cache_dir.exists():
            return
        
        cache_files = list(self.cache_dir.glob("*.json"))
        current_time = time.time()
        
        # Remove expired files
        for cache_file in cache_files:
            cache_age = current_time - cache_file.stat().st_mtime
            if cache_age > self.cache_ttl:
                try:
                    cache_file.unlink()
                    logger.debug(f"Removed expired cache file: {cache_file}")
                except OSError:
                    pass
        
        # Remove oldest files if we exceed max cache size
        remaining_files = list(self.cache_dir.glob("*.json"))
        if len(remaining_files) > self.max_cache_size:
            # Sort by modification time, oldest first
            remaining_files.sort(key=lambda f: f.stat().st_mtime)
            files_to_remove = remaining_files[:-self.max_cache_size]
            
            for cache_file in files_to_remove:
                try:
                    cache_file.unlink()
                    logger.debug(f"Removed old cache file: {cache_file}")
                except OSError:
                    pass