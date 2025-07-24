"""Audio preview player for DMX.

This module provides simple audio preview functionality using pygame
to play 30-second MP3 previews from Deezer.
"""

import os
import asyncio
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Suppress pygame welcome message and warnings before importing
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

try:
    import pygame
    import requests
    PREVIEW_AVAILABLE = True
except ImportError:
    PREVIEW_AVAILABLE = False

logger = logging.getLogger(__name__)


class PreviewPlayer:
    """Simple audio preview player using pygame."""
    
    def __init__(self):
        self.current_file: Optional[str] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self._temp_dir: Optional[str] = None
        self._setup()
    
    def _setup(self):
        """Initialize pygame mixer and temp directory."""
        if not PREVIEW_AVAILABLE:
            return
        
        try:
            # Suppress pygame welcome message and warnings
            import os
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
            
            # Initialize pygame mixer for audio playback
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            
            # Create temp directory for preview files
            self._temp_dir = tempfile.mkdtemp(prefix="dmx_previews_")
        except Exception as e:
            logger.warning(f"Failed to initialize preview player: {e}")
    
    def is_available(self) -> bool:
        """Check if preview functionality is available."""
        return PREVIEW_AVAILABLE and pygame.mixer.get_init() is not None
    
    async def play_preview(self, track: Dict[str, Any]) -> bool:
        """Play a track preview.
        
        Args:
            track: Track dictionary containing preview_url
            
        Returns:
            bool: True if preview started successfully
        """
        if not self.is_available():
            return False
        
        preview_url = track.get('preview_url')
        if not preview_url:
            return False
        
        try:
            # Stop any currently playing preview
            self.stop()
            
            # Download preview file
            preview_file = await self._download_preview(preview_url, track)
            if not preview_file:
                return False
            
            # Play the preview
            return self._play_file(preview_file)
            
        except Exception as e:
            logger.error(f"Error playing preview: {e}")
            return False
    
    async def _download_preview(self, url: str, track: Dict[str, Any]) -> Optional[str]:
        """Download preview MP3 file to temp directory."""
        if not self._temp_dir:
            return None
        
        try:
            # Create filename from track info
            safe_title = "".join(c for c in track.get('title', 'preview') if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_artist = "".join(c for c in track.get('artist', 'unknown') if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{safe_artist} - {safe_title}.mp3"[:100]  # Limit length
            filepath = os.path.join(self._temp_dir, filename)
            
            # Download file if not already cached
            if not os.path.exists(filepath):
                response = requests.get(url, timeout=10, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading preview: {e}")
            return None
    
    def _play_file(self, filepath: str) -> bool:
        """Play audio file using pygame."""
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            self.current_file = filepath
            self.is_playing = True
            self.is_paused = False
            
            return True
            
        except Exception as e:
            logger.error(f"Error playing file: {e}")
            return False
    
    def pause(self) -> bool:
        """Pause current playback."""
        if not self.is_available() or not self.is_playing:
            return False
        
        try:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
            else:
                pygame.mixer.music.pause()
                self.is_paused = True
            return True
        except Exception:
            return False
    
    def stop(self) -> bool:
        """Stop current playback."""
        if not self.is_available():
            return False
        
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_file = None
            return True
        except Exception:
            return False
    
    def is_playing_preview(self) -> bool:
        """Check if a preview is currently playing."""
        if not self.is_available():
            return False
        
        try:
            # Update playing state based on pygame status
            if self.is_playing and not pygame.mixer.music.get_busy():
                self.is_playing = False
                self.is_paused = False
            
            return self.is_playing and not self.is_paused
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current playback status."""
        return {
            'available': self.is_available(),
            'playing': self.is_playing_preview(),
            'paused': self.is_paused,
            'current_file': os.path.basename(self.current_file) if self.current_file else None
        }
    
    def cleanup(self):
        """Clean up temp files and pygame resources."""
        try:
            # Stop playback
            self.stop()
            
            # Clean up temp directory
            if self._temp_dir and os.path.exists(self._temp_dir):
                import shutil
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            
            # Quit pygame mixer
            if PREVIEW_AVAILABLE:
                pygame.mixer.quit()
                
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during deletion


# Global preview player instance
_preview_player = None


def get_preview_player() -> PreviewPlayer:
    """Get the global preview player instance."""
    global _preview_player
    if _preview_player is None:
        _preview_player = PreviewPlayer()
    return _preview_player


def cleanup_preview_player():
    """Clean up the global preview player."""
    global _preview_player
    if _preview_player is not None:
        _preview_player.cleanup()
        _preview_player = None