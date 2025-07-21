"""
Deemix client wrapper for dmx.

This module provides a simplified wrapper around the deemix library for downloading
music from Deezer. It handles authentication, quality fallback, and file management.
"""

import os
import glob
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import deemix components with fallback handling
try:
    from deemix import generateDownloadObject
    from deemix.settings import load as loadSettings
    from deemix.downloader import Downloader
    from deezer import Deezer
    DEEMIX_AVAILABLE = True
except ImportError:
    DEEMIX_AVAILABLE = False


class DeemixClient:
    """
    Simplified deemix client for music downloads.
    
    Handles:
    - Deezer authentication via ARL tokens
    - Music search (tracks, albums, artists)  
    - Downloads with quality fallback (320 → 128kbps)
    - Existing file detection to avoid re-downloads
    - Clean error handling and user feedback
    """
    
    def __init__(self, arl: str = "", quality: str = "320", output_dir: str = ""):
        """
        Initialize the deemix client.
        
        Args:
            arl: Deezer ARL authentication token
            quality: Preferred audio quality (320, 128, FLAC)
            output_dir: Directory for downloaded files
        """
        self.arl = arl
        self.quality = quality
        self.output_dir = output_dir or str(Path.home() / "Downloads" / "Music")
        self.dz = None
        self.settings = None
        self._setup()
    
    def _setup(self):
        """Set up Deezer API connection and download settings."""
        if not DEEMIX_AVAILABLE:
            return
            
        try:
            # Connect to Deezer API
            self.dz = Deezer()
            if self.arl:
                if not self.dz.login_via_arl(self.arl):
                    print("⚠️  Warning: ARL login failed. Some features may not work.")
            
            # Load deemix settings
            self.settings = loadSettings()
            self.settings['downloadLocation'] = self.output_dir
            self.settings['maxBitrate'] = self._quality_to_code(self.quality)
            
        except Exception as e:
            print(f"Warning: Failed to initialize deemix: {e}")
            self.dz = None
            self.settings = None
    
    def _quality_to_code(self, quality: str) -> int:
        """Convert quality string to deemix internal code."""
        quality_map = {"128": 1, "320": 3, "FLAC": 9}
        return quality_map.get(quality, 3)  # Default to 320kbps
    
    def _code_to_quality(self, code: int) -> str:
        """Convert deemix code back to readable quality."""
        code_map = {1: "128kbps MP3", 3: "320kbps MP3", 9: "FLAC"}
        return code_map.get(code, f"Quality {code}")
    
    def is_available(self) -> bool:
        """Check if deemix is properly initialized."""
        return self.dz is not None and self.settings is not None
    
    # Search Methods
    def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tracks on Deezer."""
        if not self.dz:
            return []
        
        try:
            results = self.dz.api.search(query, "track", limit=limit)
            return self._format_tracks(results.get('data', []))
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_albums(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for albums on Deezer.
        
        Note: Deezer API returns track objects for album searches,
        so we extract unique albums from track results.
        """
        if not self.dz:
            return []
        
        try:
            results = self.dz.api.search(query, "album", limit=limit)
            tracks = results.get('data', [])
            return self._extract_albums_from_tracks(tracks)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_artists(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for artists on Deezer."""
        if not self.dz:
            return []
        
        try:
            # Search for tracks and extract unique artists
            # Note: Deezer API search with type "artist" returns tracks, not artist objects
            track_results = self.dz.api.search(query, "track", limit=limit*2)
            track_data = track_results.get('data', [])
            
            # Extract unique artists and get their full details
            artist_ids = set()
            artists_data = []
            
            for track in track_data:
                artist_info = track.get('artist', {})
                artist_id = artist_info.get('id')
                
                if artist_id and artist_id not in artist_ids:
                    artist_ids.add(artist_id)
                    try:
                        # Get full artist details from API
                        full_artist = self.dz.api.get_artist(artist_id)
                        artists_data.append(full_artist)
                    except:
                        # Fallback to basic artist info from track
                        artists_data.append(artist_info)
                    
                    # Limit results
                    if len(artists_data) >= limit:
                        break
            
            formatted_artists = self._format_artists(artists_data)
            # Sort by fan count (highest to lowest)
            formatted_artists.sort(key=lambda x: x.get('fans', 0), reverse=True)
            return formatted_artists
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def _format_tracks(self, tracks: List[Dict]) -> List[Dict[str, Any]]:
        """Format track search results for display."""
        formatted = []
        for track in tracks:
            formatted.append({
                'id': track.get('id'),
                'title': track.get('title', 'Unknown'),
                'artist': track.get('artist', {}).get('name', 'Unknown'),
                'album': track.get('album', {}).get('title', 'Unknown'),
                'duration': self._format_duration(track.get('duration', 0)),
                'type': 'track',
                'url': f"https://www.deezer.com/track/{track.get('id')}"
            })
        return formatted
    
    def _extract_albums_from_tracks(self, tracks: List[Dict]) -> List[Dict[str, Any]]:
        """Extract unique albums from track search results."""
        albums = {}
        
        for track in tracks:
            album_info = track.get('album', {})
            album_id = album_info.get('id')
            
            if album_id and album_id not in albums:
                # Get full album details to get accurate track count
                try:
                    album_details = self.dz.api.get_album(album_id)
                    track_count = album_details.get('nb_tracks', 0)
                except:
                    track_count = 0
                
                albums[album_id] = {
                    'id': album_id,
                    'title': album_info.get('title', 'Unknown'),
                    'artist': track.get('artist', {}).get('name', 'Unknown'),
                    'tracks': track_count,
                    'type': 'album',
                    'url': f"https://www.deezer.com/album/{album_id}"
                }
        
        return list(albums.values())
    
    def _extract_artists_from_tracks(self, tracks: List[Dict]) -> List[Dict[str, Any]]:
        """Extract unique artists from track search results."""
        artists = {}
        
        for track in tracks:
            artist_info = track.get('artist', {})
            artist_id = artist_info.get('id')
            
            if artist_id and artist_id not in artists:
                artists[artist_id] = artist_info
        
        return list(artists.values())
    
    def _format_artists(self, artists: List[Dict]) -> List[Dict[str, Any]]:
        """Format artist search results for display."""
        formatted = []
        for artist in artists:
            formatted.append({
                'id': artist.get('id'),
                'name': artist.get('name', 'Unknown'),
                'albums': artist.get('nb_album', 0),
                'fans': artist.get('nb_fan', 0),
                'type': 'artist',
                'url': f"https://www.deezer.com/artist/{artist.get('id')}"
            })
        return formatted
    
    def _format_duration(self, seconds: int) -> str:
        """Convert seconds to MM:SS format."""
        if not seconds:
            return "0:00"
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def get_artist_profile(self, artist_id: str) -> Dict[str, Any]:
        """Get artist profile with top songs and albums."""
        if not self.dz:
            return {}
        
        try:
            # Get artist info
            artist_info = self.dz.api.get_artist(artist_id)
            
            # Get top tracks
            try:
                top_tracks_response = self.dz.api.get_artist_top(artist_id, limit=10)
                top_tracks = self._format_tracks(top_tracks_response.get('data', []))
            except:
                top_tracks = []
            
            # Get albums
            try:
                albums_response = self.dz.api.get_artist_albums(artist_id, limit=500)  # Get all albums
                albums = []
                for album in albums_response.get('data', []):
                    album_id = album.get('id')
                    try:
                        # Get full album details to get track count
                        full_album = self.dz.api.get_album(album_id)
                        track_count = full_album.get('nb_tracks', 0)
                    except:
                        track_count = 0
                    
                    albums.append({
                        'id': album_id,
                        'title': album.get('title', 'Unknown'),
                        'tracks': track_count,
                        'type': 'album',
                        'url': f"https://www.deezer.com/album/{album_id}"
                    })
            except:
                albums = []
            
            return {
                'artist': {
                    'id': artist_info.get('id'),
                    'name': artist_info.get('name', 'Unknown'),
                    'albums': artist_info.get('nb_album', 0),
                    'fans': artist_info.get('nb_fan', 0)
                },
                'top_tracks': top_tracks,
                'albums': albums
            }
        except Exception as e:
            print(f"Error fetching artist profile: {e}")
            return {}
    
    # Download Methods
    def download(self, url: str) -> bool:
        """
        Download music from Deezer URL with quality fallback.
        
        Process:
        1. Check if files already exist (skip download)
        2. Try requested quality, fallback to lower if needed
        3. Verify download success by checking created files
        
        Args:
            url: Deezer URL (track, album, or playlist)
            
        Returns:
            bool: True if download succeeded or files already exist
        """
        if not self.is_available():
            print("Error: Deemix not properly initialized")
            return False
        
        if not self.arl:
            print("Error: No ARL token configured. Please set your ARL token first.")
            return False
        
        # Check if content already exists
        if self._check_existing_content(url):
            return True
        
        # Try download with quality fallback
        return self._attempt_download(url)
    
    def _check_existing_content(self, url: str) -> bool:
        """Check if content from URL is already downloaded."""
        try:
            if '/album/' in url:
                album_id = url.split('/album/')[-1].split('?')[0]
                return self._check_existing_album(album_id)
            elif '/track/' in url:
                track_id = url.split('/track/')[-1].split('?')[0]  
                return self._check_existing_track(track_id)
        except Exception:
            pass  # If check fails, proceed with download
        
        return False
    
    def _check_existing_album(self, album_id: str) -> bool:
        """Check if album is already downloaded."""
        try:
            # Get album info
            album_info = self.dz.api.get_album(album_id)
            album_title = album_info.get('title', '')
            artist_name = album_info.get('artist', {}).get('name', '')
            expected_tracks = album_info.get('nb_tracks', 0)
            
            # Look for album folder
            folder_name = f"{artist_name} - {album_title}"
            folder_path = os.path.join(self.output_dir, folder_name)
            
            if os.path.exists(folder_path):
                # Count audio files in folder
                audio_files = [f for f in os.listdir(folder_path) 
                             if f.endswith(('.mp3', '.flac', '.m4a')) 
                             and os.path.getsize(os.path.join(folder_path, f)) > 0]
                
                # Check if we have at least 80% of expected tracks
                if len(audio_files) >= expected_tracks * 0.8:
                    print(f"✓ Album already downloaded: {album_title} by {artist_name} ({len(audio_files)} files)")
                    print(f"  Located at: {folder_path}")
                    return True
        except Exception:
            pass
        
        return False
    
    def _check_existing_track(self, track_id: str) -> bool:
        """Check if track is already downloaded."""
        try:
            # Get track info  
            track_info = self.dz.api.get_track(track_id)
            track_title = track_info.get('title', '')
            artist_name = track_info.get('artist', {}).get('name', '')
            
            # Search for existing file
            for root, _, files in os.walk(self.output_dir):
                for file in files:
                    if (file.endswith(('.mp3', '.flac', '.m4a')) and
                        track_title.lower() in file.lower() and 
                        artist_name.lower() in file.lower()):
                        file_path = os.path.join(root, file)
                        if os.path.getsize(file_path) > 0:
                            print(f"✓ Track already downloaded: {track_title} by {artist_name}")
                            print(f"  Located at: {file_path}")
                            return True
        except Exception:
            pass
        
        return False
    
    def _attempt_download(self, url: str) -> bool:
        """Attempt download with quality fallback."""
        print(f"Attempting to download: {url}")
        
        # Quality fallback: try 320 → 128kbps
        qualities = [3, 1]  # 320kbps, 128kbps codes
        if self.settings['maxBitrate'] not in qualities:
            qualities.insert(0, self.settings['maxBitrate'])
        
        download_start_time = time.time()
        
        for quality_code in qualities:
            if self._try_quality(url, quality_code, download_start_time):
                return True
        
        # All qualities failed
        print("Failed to download at any available quality level")
        print("This might mean:")
        print("  - Your account doesn't have premium access")
        print("  - The track is not available for download in your region") 
        print("  - Your ARL token has limited permissions")
        return False
    
    def _try_quality(self, url: str, quality_code: int, start_time: float) -> bool:
        """Try downloading at specific quality."""
        quality_name = self._code_to_quality(quality_code)
        
        if quality_code != self.settings['maxBitrate']:
            print(f"Trying lower quality: {quality_name}")
        else:
            print(f"Trying quality: {quality_name}")
        
        try:
            # Generate download object
            downloadObject = generateDownloadObject(self.dz, url, quality_code, None, self.settings)
            if not downloadObject:
                return False
            
            title = self._extract_title(downloadObject)
            print(f"Starting download: {title} ({quality_name})")
            
            # Create download listener for minimal feedback
            listener = self._create_listener()
            
            # Configure settings to prevent errors.txt
            temp_settings = self.settings.copy()
            temp_settings['logErrors'] = False
            temp_settings['logSearched'] = False
            
            # Perform download
            downloader = Downloader(self.dz, downloadObject, temp_settings, listener)
            downloader.start()
            
            # Wait briefly for download to complete
            time.sleep(3)
            
            # Check if download succeeded by looking for new files
            if self._verify_download_success(start_time):
                return True
            
        except Exception as e:
            error_msg = str(e).lower()
            # Only continue to next quality if it's a bitrate/quality error
            if any(keyword in error_msg for keyword in ['bitrate', 'stream', 'quality', 'desired']):
                return False
            else:
                print(f"Download error: {e}")
                return False
        
        return False
    
    def _create_listener(self):
        """Create a simple download listener for minimal progress feedback."""
        class SimpleListener:
            def __init__(self):
                self.shown_start = False
            
            def send(self, event, data=None):
                # Only show "Starting download..." once
                if event == 'downloadInfo' and isinstance(data, dict):
                    state = data.get('state', '')
                    if state == 'downloading' and not self.shown_start:
                        print("Starting download...")
                        self.shown_start = True
        
        return SimpleListener()
    
    def _extract_title(self, downloadObject) -> str:
        """Extract title from download object."""
        try:
            if hasattr(downloadObject, 'title'):
                return downloadObject.title
            elif hasattr(downloadObject, 'get'):
                return downloadObject.get('title', 'Unknown')
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _verify_download_success(self, start_time: float) -> bool:
        """Verify download succeeded by checking for new files."""
        new_files = []
        
        # Look for audio files created after download started
        for root, _, files in os.walk(self.output_dir):
            for file in files:
                if file.endswith(('.mp3', '.flac', '.m4a')):
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file was created after we started and has content
                        if (os.path.getmtime(file_path) > start_time and 
                            os.path.getsize(file_path) > 0):
                            new_files.append(file_path)
                    except OSError:
                        continue
        
        if new_files:
            if len(new_files) == 1:
                print(f"✓ Downloaded: {os.path.basename(new_files[0])}")
            else:
                print(f"✓ Downloaded {len(new_files)} files")
            return True
        
        return False
    
    # Utility Methods
    def get_supported_qualities(self) -> List[str]:
        """Get list of supported quality settings."""
        return ["128", "320", "FLAC"]
    
    def is_valid_quality(self, quality: str) -> bool:
        """Check if quality setting is valid."""
        return quality in self.get_supported_qualities()