"""Music client for search and download functionality."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from dmx.api_client import APIClient

logger = logging.getLogger(__name__)


class MusicClient:
    """Music client with search and download capabilities."""
    
    def __init__(self, arl: str = "", quality: str = "320", output_dir: str = "", config_dir: Optional[Path] = None):
        self.arl = arl
        self.quality = quality
        self.output_dir = output_dir or str(Path.home() / "Downloads" / "Music")
        self.config_dir = config_dir
        
        # Initialize clients
        self.api_client: Optional[APIClient] = None
        self.deemix_client = None
        
        self.client_status = {
            'api_client': False,
            'deemix_client': False
        }
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available clients."""
        # Try to initialize deemix client
        try:
            from dmx.deemix_client import DeemixClient
            self.deemix_client = DeemixClient(self.arl, self.quality, self.output_dir)
            self.client_status['deemix_client'] = self.deemix_client.is_available()
            logger.info(f"Deemix client initialized: {self.client_status['deemix_client']}")
        except ImportError as e:
            logger.warning(f"Deemix not available: {e}")
            self.deemix_client = None
        except Exception as e:
            logger.error(f"Failed to initialize deemix client: {e}")
            self.deemix_client = None
        
        logger.info(f"Client status: {self.client_status}")
    
    async def _ensure_api_client(self):
        """Ensure API client is initialized."""
        if self.api_client is None:
            try:
                self.api_client = APIClient(self.config_dir)
                await self.api_client.__aenter__()
                self.client_status['api_client'] = True
                logger.info("API client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize API client: {e}")
                self.api_client = None
                self.client_status['api_client'] = False
    
    def is_available(self) -> bool:
        """Check if any client is available."""
        return any(self.client_status.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of all clients."""
        return {
            'available': self.is_available(),
            'clients': self.client_status,
            'primary_search': 'deemix_client' if self.client_status['deemix_client'] else 'api_client',
            'download_capable': self.client_status['deemix_client']
        }
    
    async def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tracks."""
        # Try deemix client first if available (for downloadable URLs)
        if self.deemix_client and self.client_status['deemix_client']:
            try:
                results = self.deemix_client.search_tracks(query, limit)
                if results:
                    logger.debug(f"Deemix search returned {len(results)} tracks")
                    return results
            except Exception as e:
                logger.warning(f"Deemix track search failed: {e}")
        
        # Try API client as fallback
        await self._ensure_api_client()
        if self.api_client:
            try:
                results = await self.api_client.search_tracks(query, limit)
                if results:
                    logger.debug(f"API search returned {len(results)} tracks")
                    return results
            except Exception as e:
                logger.warning(f"API track search failed: {e}")
        
        # No results available
        logger.warning("No search clients available")
        return []
    
    async def search_albums(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for albums."""
        # Try deemix client first if available (for downloadable URLs)
        if self.deemix_client and self.client_status['deemix_client']:
            try:
                results = self.deemix_client.search_albums(query, limit)
                if results:
                    logger.debug(f"Deemix search returned {len(results)} albums")
                    return results
            except Exception as e:
                logger.warning(f"Deemix album search failed: {e}")
        
        # Try API client as fallback
        await self._ensure_api_client()
        if self.api_client:
            try:
                results = await self.api_client.search_albums(query, limit)
                if results:
                    logger.debug(f"API search returned {len(results)} albums")
                    return results
            except Exception as e:
                logger.warning(f"API album search failed: {e}")
        
        # No results available
        logger.warning("No search clients available")
        return []
    
    async def search_artists(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for artists."""
        # Try deemix client first if available (for downloadable URLs)
        if self.deemix_client and self.client_status['deemix_client']:
            try:
                results = self.deemix_client.search_artists(query, limit)
                if results:
                    logger.debug(f"Deemix search returned {len(results)} artists")
                    return results
            except Exception as e:
                logger.warning(f"Deemix artist search failed: {e}")
        
        # Try API client as fallback
        await self._ensure_api_client()
        if self.api_client:
            try:
                results = await self.api_client.search_artists(query, limit)
                if results:
                    logger.debug(f"API search returned {len(results)} artists")
                    return results
            except Exception as e:
                logger.warning(f"API artist search failed: {e}")
        
        # No results available
        logger.warning("No search clients available")
        return []
    
    def download(self, url: str) -> bool:
        """Download with real deemix client only."""
        # Only use deemix client for downloads
        if self.deemix_client and self.client_status['deemix_client']:
            try:
                result = self.deemix_client.download(url)
                if result:
                    logger.info("Download completed via deemix")
                    return True
                else:
                    logger.warning("Deemix download failed - check ARL token and content availability")
            except Exception as e:
                logger.error(f"Deemix download failed: {e}")
        else:
            print("Error: Deemix client not available. Cannot download without proper setup.")
            if not self.deemix_client:
                print("Deemix client not initialized - check your deemix installation")
            elif not self.client_status['deemix_client']:
                print("Deemix client not properly configured - check your ARL token")
        
        return False
    
    def get_supported_qualities(self) -> List[str]:
        """Get supported quality settings."""
        if self.deemix_client:
            return self.deemix_client.get_supported_qualities()
        return ["128", "320", "FLAC"]
    
    def is_valid_quality(self, quality: str) -> bool:
        """Check if quality is valid."""
        return quality in self.get_supported_qualities()
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.api_client:
            try:
                await self.api_client.__aexit__(None, None, None)
                if hasattr(self.api_client, 'cleanup_cache'):
                    self.api_client.cleanup_cache()
                logger.info("API client cleanup completed")
            except Exception as e:
                logger.error(f"API client cleanup failed: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_api_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()