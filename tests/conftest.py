"""Pytest configuration and fixtures."""

import asyncio
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock

from dmx.config import Config
from dmx.error_handler import ErrorHandler
from dmx.music_client import MusicClient


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_config_dir():
    """Create a temporary configuration directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_config_dir):
    """Create a test configuration."""
    config = Config(str(temp_config_dir))
    config.arl = "test_arl"
    config.quality = "320"
    config.output_dir = str(temp_config_dir / "downloads")
    config.search_limit = 10
    return config


@pytest.fixture
def error_handler(temp_config_dir):
    """Create an error handler for testing."""
    return ErrorHandler(debug_mode=True, log_file=temp_config_dir / "test.log")


@pytest.fixture
def mock_api_client():
    """Mock API client."""
    client = AsyncMock()
    client.search_tracks.return_value = [
        {
            'id': 'test_track_1',
            'title': 'Test Track 1',
            'artist': 'Test Artist 1',
            'album': 'Test Album 1',
            'duration': '3:30',
            'type': 'track',
            'url': 'https://musicbrainz.org/recording/test_1'
        }
    ]
    client.search_albums.return_value = [
        {
            'id': 'test_album_1',
            'title': 'Test Album 1',
            'artist': 'Test Artist 1',
            'tracks': 12,
            'type': 'album',
            'url': 'https://musicbrainz.org/release/test_1'
        }
    ]
    client.search_artists.return_value = [
        {
            'id': 'test_artist_1',
            'name': 'Test Artist 1',
            'albums': 5,
            'fans': 1000,
            'type': 'artist',
            'url': 'https://musicbrainz.org/artist/test_1'
        }
    ]
    return client


@pytest.fixture
def mock_music_client(test_config, temp_config_dir):
    """Mock music client."""
    client = MusicClient(
        arl=test_config.arl,
        quality=test_config.quality,
        output_dir=test_config.output_dir,
        config_dir=temp_config_dir
    )
    
    # Mock the methods
    client.search_tracks = AsyncMock(return_value=[
        {
            'id': 'test_track_1',
            'title': 'Test Track 1',
            'artist': 'Test Artist 1',
            'album': 'Test Album 1',
            'duration': '3:30',
            'type': 'track',
            'url': 'https://test.com/track/1'
        }
    ])
    
    client.search_albums = AsyncMock(return_value=[
        {
            'id': 'test_album_1',
            'title': 'Test Album 1',
            'artist': 'Test Artist 1',
            'tracks': 12,
            'type': 'album',
            'url': 'https://test.com/album/1'
        }
    ])
    
    client.search_artists = AsyncMock(return_value=[
        {
            'id': 'test_artist_1',
            'name': 'Test Artist 1',
            'albums': 5,
            'fans': 1000,
            'type': 'artist',
            'url': 'https://test.com/artist/1'
        }
    ])
    
    client.download = Mock(return_value=True)
    client.is_available = Mock(return_value=True)
    client.get_status = Mock(return_value={
        'available': True,
        'clients': {'deemix_client': True, 'api_client': False},
        'primary_search': 'deemix_client',
        'download_capable': True
    })
    
    return client


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return {
        'tracks': [
            {
                'id': 'track_1',
                'title': 'Sample Track 1',
                'artist': 'Sample Artist 1',
                'album': 'Sample Album 1',
                'duration': '3:45',
                'type': 'track',
                'url': 'https://test.com/track/1'
            },
            {
                'id': 'track_2',
                'title': 'Sample Track 2',
                'artist': 'Sample Artist 2',
                'album': 'Sample Album 2',
                'duration': '4:20',
                'type': 'track',
                'url': 'https://test.com/track/2'
            }
        ],
        'albums': [
            {
                'id': 'album_1',
                'title': 'Sample Album 1',
                'artist': 'Sample Artist 1',
                'tracks': 12,
                'type': 'album',
                'url': 'https://test.com/album/1'
            }
        ],
        'artists': [
            {
                'id': 'artist_1',
                'name': 'Sample Artist 1',
                'albums': 5,
                'fans': 50000,
                'type': 'artist',
                'url': 'https://test.com/artist/1'
            }
        ]
    }