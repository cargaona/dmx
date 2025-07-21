"""Tests for API client functionality."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from aioresponses import aioresponses

from dmx.api_client import APIClient, APIError, RateLimitError


@pytest.mark.asyncio
class TestAPIClient:
    """Test API client functionality."""
    
    async def test_api_client_context_manager(self, temp_config_dir):
        """Test API client context manager."""
        async with APIClient(temp_config_dir) as client:
            assert client.session is not None
            assert isinstance(client.session, aiohttp.ClientSession)
    
    async def test_rate_limiting(self, temp_config_dir):
        """Test rate limiting functionality."""
        async with APIClient(temp_config_dir) as client:
            client.rate_limit.requests_per_second = 2.0
            
            start_time = asyncio.get_event_loop().time()
            
            # Make multiple requests
            await client._rate_limit()
            await client._rate_limit()
            await client._rate_limit()
            
            end_time = asyncio.get_event_loop().time()
            
            # Should take at least 0.5 seconds for 3 requests at 2 RPS
            assert end_time - start_time >= 0.4
    
    @aioresponses()
    async def test_musicbrainz_search_tracks(self, m, temp_config_dir):
        """Test MusicBrainz track search."""
        # Mock response
        mock_response = {
            "recordings": [
                {
                    "id": "test-id-1",
                    "title": "Test Track",
                    "length": 210000,  # 3:30 in milliseconds
                    "artist-credit": [{"name": "Test Artist"}],
                    "releases": [{"title": "Test Album"}],
                    "score": 100
                }
            ]
        }
        
        m.get(
            "https://musicbrainz.org/ws/2/recording",
            payload=mock_response
        )
        
        async with APIClient(temp_config_dir) as client:
            results = await client.search_tracks("test query", 10)
            
            assert len(results) == 1
            assert results[0]['title'] == 'Test Track'
            assert results[0]['artist'] == 'Test Artist'
            assert results[0]['album'] == 'Test Album'
            assert results[0]['duration'] == '3:30'
            assert results[0]['type'] == 'track'
    
    @aioresponses()
    async def test_musicbrainz_search_albums(self, m, temp_config_dir):
        """Test MusicBrainz album search."""
        mock_response = {
            "releases": [
                {
                    "id": "test-album-id",
                    "title": "Test Album",
                    "track-count": 12,
                    "artist-credit": [{"name": "Test Artist"}],
                    "score": 95
                }
            ]
        }
        
        m.get(
            "https://musicbrainz.org/ws/2/release",
            payload=mock_response
        )
        
        async with APIClient(temp_config_dir) as client:
            results = await client.search_albums("test album", 10)
            
            assert len(results) == 1
            assert results[0]['title'] == 'Test Album'
            assert results[0]['artist'] == 'Test Artist'
            assert results[0]['tracks'] == 12
            assert results[0]['type'] == 'album'
    
    @aioresponses()
    async def test_musicbrainz_search_artists(self, m, temp_config_dir):
        """Test MusicBrainz artist search."""
        mock_response = {
            "artists": [
                {
                    "id": "test-artist-id",
                    "name": "Test Artist",
                    "score": 98
                }
            ]
        }
        
        m.get(
            "https://musicbrainz.org/ws/2/artist",
            payload=mock_response
        )
        
        async with APIClient(temp_config_dir) as client:
            results = await client.search_artists("test artist", 10)
            
            assert len(results) == 1
            assert results[0]['name'] == 'Test Artist'
            assert results[0]['type'] == 'artist'
    
    async def test_caching(self, temp_config_dir):
        """Test caching functionality."""
        async with APIClient(temp_config_dir) as client:
            # Test cache key generation
            key = client._get_cache_key("test", {"param": "value"})
            assert isinstance(key, str)
            assert len(key) == 32  # MD5 hash length
            
            # Test cache write/read
            test_data = {"test": "data"}
            client._write_cache(key, test_data)
            
            cached_data = client._read_cache(key)
            assert cached_data == test_data
    
    @aioresponses()
    async def test_api_error_handling(self, m, temp_config_dir):
        """Test API error handling."""
        # Test 404 error
        m.get(
            "https://musicbrainz.org/ws/2/recording",
            status=404
        )
        
        async with APIClient(temp_config_dir) as client:
            results = await client.search_tracks("nonexistent", 10)
            assert results == []
    
    @aioresponses()
    async def test_rate_limit_error(self, m, temp_config_dir):
        """Test rate limit error handling."""
        m.get(
            "https://musicbrainz.org/ws/2/recording",
            status=429
        )
        
        async with APIClient(temp_config_dir) as client:
            results = await client.search_tracks("test", 10)
            assert results == []
    
    def test_duration_formatting(self, temp_config_dir):
        """Test duration formatting."""
        client = APIClient(temp_config_dir)
        
        assert client._format_duration(0) == "0:00"
        assert client._format_duration(90000) == "1:30"
        assert client._format_duration(210000) == "3:30"
        assert client._format_duration(None) == "0:00"
    
    def test_cache_cleanup(self, temp_config_dir):
        """Test cache cleanup functionality."""
        import time
        
        with APIClient(temp_config_dir) as client:
            # Create some cache files
            client._write_cache("key1", {"data": 1})
            client._write_cache("key2", {"data": 2})
            
            # Mock old file
            old_file = client._get_cache_file("old_key")
            old_file.touch()
            # Set modification time to 2 hours ago
            old_time = time.time() - 7200
            old_file.touch(times=(old_time, old_time))
            
            # Cleanup
            client.cleanup_cache()
            
            # Old file should be removed
            assert not old_file.exists()
            
            # New files should remain
            assert client._get_cache_file("key1").exists()
            assert client._get_cache_file("key2").exists()