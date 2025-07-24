"""Interactive search session inspired by beets."""

import sys
import asyncio
from typing import List, Dict, Any, Optional
from colorama import init, Fore, Style, Back
import re
import logging

from dmx.config import Config
from dmx.music_client import MusicClient
from dmx.error_handler import ErrorHandler, ErrorContext, ErrorSeverity, InputValidator, handle_errors

# Initialize colorama for cross-platform color support
init()

logger = logging.getLogger(__name__)


class InteractiveSession:
    """Interactive search and download session."""
    
    def __init__(self, config: Config):
        self.config = config
        try:
            self.error_handler = ErrorHandler(
                debug_mode=config.get('debug', False),
                log_file=config.config_dir / "logs" / "dmx.log"
            )
        except Exception:
            # Fallback error handler
            self.error_handler = ErrorHandler(debug_mode=False)
        
        # Initialize music client
        try:
            self.client = MusicClient(
                arl=config.arl,
                quality=config.quality,
                output_dir=config.output_dir,
                config_dir=config.config_dir
            )
        except Exception as e:
            logger.error(f"Failed to initialize music client: {e}")
            raise
        
        self.current_results: List[Dict[str, Any]] = []
        self.current_mode = "tracks"  # tracks, albums, artists
        self.current_artist_albums: List[Dict[str, Any]] = []  # For artist profile view
        self.current_artist_info: Dict[str, Any] = {}  # Current artist info
        self.search_history: List[str] = []
        try:
            self.validator = InputValidator()
        except Exception:
            self.validator = None
    
    def start(self, initial_query: str = ""):
        """Start interactive session."""
        return asyncio.run(self._async_start(initial_query))
    
    async def _async_start(self, initial_query: str = ""):
        """Async start method."""
        try:
            # Check if client supports async context manager
            if hasattr(self.client, '__aenter__'):
                async with self.client:
                    return await self._run_session(initial_query)
            else:
                # Fallback for mock client
                return await self._run_session(initial_query)
        except Exception as e:
            context = ErrorContext("session_start")
            self.error_handler.handle_error(e, context, ErrorSeverity.CRITICAL)
            return False
    
    async def _run_session(self, initial_query: str = ""):
        """Run the interactive session."""
        if not self.client.is_available():
            print(f"{Fore.RED}Error: No music services available. Please check your configuration.{Style.RESET_ALL}")
            return False
        
        self._print_welcome()
        
        if initial_query:
            try:
                if self.validator:
                    validated_query = self.validator.validate_search_query(initial_query)
                else:
                    validated_query = initial_query.strip()
                await self._search(validated_query)
            except Exception as e:
                context = ErrorContext("initial_search", initial_query)
                self.error_handler.handle_error(e, context)
        
        await self._main_loop()
        return True
    
    def _print_welcome(self):
        """Print welcome message and help."""
        print(f"\n{Fore.CYAN}🎵 dmx Interactive Search{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Quality: {self.config.quality} | Output: {self.config.output_dir}{Style.RESET_ALL}")
        
        # Show client status
        status = self.client.get_status()
        
        if status['download_capable']:
            print(f"{Fore.GREEN}✓ Download capability available{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Download capability limited (check deemix and ARL setup){Style.RESET_ALL}")
        
        if not self.config.arl:
            print(f"{Fore.YELLOW}⚠️  Warning: No ARL configured. Downloads will not work.{Style.RESET_ALL}")
        
        print(f"\n{Fore.BLUE}Commands:{Style.RESET_ALL}")
        print("  [number]     - Download item (tracks/albums) or view profile (artists)")
        print("  [1,3,5]      - Download multiple items (comma-separated)")
        print("  [1-5]        - Download range of items")
        print("  [1,3-5,8]    - Download mixed selection")
        print("  all / *      - Download all current results")
        print("  s <query>    - Search for tracks")
        print("  sa <query>   - Search for albums") 
        print("  st <query>   - Search for artists")
        print("  m [mode]     - Switch mode (tracks/albums/artists)")
        print("  l            - List current results")
        print("  back/b       - Go back from artist profile to search results")
        print("  status       - Show system status")
        print("  h            - Show this help")
        print("  q            - Quit")
        print()
    
    async def _main_loop(self):
        """Main interactive loop."""
        while True:
            try:
                # Show current mode in prompt
                mode_color = self._get_mode_color()
                if self.current_artist_albums:
                    # In artist profile view
                    artist_name = self.current_artist_info.get('name', 'Artist')
                    prompt = f"{mode_color}[{artist_name} Albums]{Style.RESET_ALL} > "
                else:
                    prompt = f"{mode_color}[{self.current_mode}]{Style.RESET_ALL} > "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                if not await self._handle_command(user_input):
                    break
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            except EOFError:
                break
            except Exception as e:
                context = ErrorContext("main_loop", user_input)
                self.error_handler.handle_error(e, context)
    
    async def _handle_command(self, user_input: str) -> bool:
        """Handle user command. Returns False to exit."""
        try:
            # Check if it's a selection (number, range, or 'all')
            selection_indices = self._parse_selection_input(user_input)
            if selection_indices is not None:
                if self.current_mode == "artists" and not self.current_artist_albums:
                    # For artists mode, only allow single selection to view profile
                    if len(selection_indices) == 1:
                        return await self._view_artist_profile(selection_indices[0])
                    else:
                        print(f"{Fore.RED}Artist mode only supports single selection to view profiles.{Style.RESET_ALL}")
                        return True
                elif self.current_artist_albums:
                    # Download album(s) from artist profile view
                    return await self._download_albums_from_artist(selection_indices)
                else:
                    # Download item(s)
                    return await self._download_by_numbers(selection_indices)
            
            # Parse command and arguments
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd == 'q' or cmd == 'quit':
                print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                return False
            
            elif cmd == 'h' or cmd == 'help':
                self._print_welcome()
            
            elif cmd == 'status':
                self._show_status()
            
            elif cmd == 's' or cmd == 'search':
                if not args:
                    print(f"{Fore.RED}Usage: s <query>{Style.RESET_ALL}")
                else:
                    self.current_mode = "tracks"
                    self.current_artist_albums = []  # Clear artist profile
                    self.current_artist_info = {}
                    await self._search(args)
            
            elif cmd == 'sa':
                if not args:
                    print(f"{Fore.RED}Usage: sa <query>{Style.RESET_ALL}")
                else:
                    self.current_mode = "albums"
                    self.current_artist_albums = []  # Clear artist profile
                    self.current_artist_info = {}
                    await self._search(args)
            
            elif cmd == 'st':
                if not args:
                    print(f"{Fore.RED}Usage: st <query>{Style.RESET_ALL}")
                else:
                    self.current_mode = "artists"
                    self.current_artist_albums = []  # Clear artist profile
                    self.current_artist_info = {}
                    await self._search(args)
            
            elif cmd == 'm' or cmd == 'mode':
                if args in ['tracks', 'albums', 'artists']:
                    self.current_mode = args
                    self.current_artist_albums = []  # Clear artist profile
                    self.current_artist_info = {}
                    print(f"{Fore.GREEN}Switched to {args} mode{Style.RESET_ALL}")
                elif not args:
                    print(f"{Fore.BLUE}Current mode: {self.current_mode}{Style.RESET_ALL}")
                    print("Available modes: tracks, albums, artists")
                else:
                    print(f"{Fore.RED}Invalid mode: {args}{Style.RESET_ALL}")
            
            elif cmd == 'l' or cmd == 'list':
                if self.current_artist_albums:
                    self._display_artist_albums()
                else:
                    self._display_results()
            
            elif cmd == 'back' or cmd == 'b':
                if self.current_artist_albums:
                    # Exit artist profile view
                    self.current_artist_albums = []
                    self.current_artist_info = {}
                    print(f"{Fore.GREEN}Back to artist search results{Style.RESET_ALL}")
                    self._display_results()
                else:
                    print(f"{Fore.YELLOW}Nothing to go back to{Style.RESET_ALL}")
            
            else:
                # Treat as search query for current mode
                self.current_artist_albums = []  # Clear artist profile
                self.current_artist_info = {}
                await self._search(user_input)
            
            return True
        
        except Exception as e:
            context = ErrorContext("command_handling", user_input)
            self.error_handler.handle_error(e, context)
            return True
    
    async def _search(self, query: str):
        """Perform search based on current mode."""
        try:
            # Validate query
            if self.validator:
                validated_query = self.validator.validate_search_query(query)
            else:
                validated_query = query.strip()
            
            print(f"{Fore.BLUE}Searching for {self.current_mode}: {validated_query}...{Style.RESET_ALL}")
            
            # Perform search based on mode
            # Check if client has async methods or fallback to sync
            if hasattr(self.client, 'search_tracks') and asyncio.iscoroutinefunction(self.client.search_tracks):
                # Async client
                if self.current_mode == "tracks":
                    results = await self.client.search_tracks(validated_query, self.config.search_limit)
                elif self.current_mode == "albums":
                    results = await self.client.search_albums(validated_query, self.config.search_limit)
                elif self.current_mode == "artists":
                    results = await self.client.search_artists(validated_query, self.config.search_limit)
                else:
                    results = []
            else:
                # Sync client (mock)
                if self.current_mode == "tracks":
                    results = self.client.search_tracks(validated_query, self.config.search_limit)
                elif self.current_mode == "albums":
                    results = self.client.search_albums(validated_query, self.config.search_limit)
                elif self.current_mode == "artists":
                    results = self.client.search_artists(validated_query, self.config.search_limit)
                else:
                    results = []
            
            self.current_results = results
            self.search_history.append(validated_query)
            
            if results:
                self._display_results()
            else:
                print(f"{Fore.YELLOW}No results found.{Style.RESET_ALL}")
                
        except Exception as e:
            context = ErrorContext("search", query, additional_info={'mode': self.current_mode})
            self.error_handler.handle_error(e, context)
    
    def _show_status(self):
        """Show detailed system status."""
        print(f"\n{Fore.CYAN}System Status:{Style.RESET_ALL}")
        
        status = self.client.get_status()
        print(f"  Available: {'✓' if status.get('available', True) else '✗'}")
        print(f"  Primary search: {status.get('primary_search', 'none')}")
        print(f"  Download capable: {'✓' if status.get('download_capable', False) else '✗'}")
        
        if 'clients' in status:
            print(f"\n{Fore.CYAN}Client Status:{Style.RESET_ALL}")
            for client, available in status['clients'].items():
                status_icon = '✓' if available else '✗'
                print(f"  {client}: {status_icon}")
        
        print(f"\n{Fore.CYAN}Configuration:{Style.RESET_ALL}")
        print(f"  Quality: {self.config.quality}")
        print(f"  Output directory: {self.config.output_dir}")
        print(f"  Search limit: {self.config.search_limit}")
        print(f"  ARL configured: {'✓' if self.config.arl else '✗'}")
        
        # Error statistics
        if self.error_handler:
            error_stats = self.error_handler.get_error_stats()
            if error_stats:
                print(f"\n{Fore.CYAN}Error Statistics:{Style.RESET_ALL}")
                for error_type, count in error_stats.items():
                    print(f"  {error_type}: {count}")
        
        print()
    
    def _display_results(self):
        """Display current search results."""
        if not self.current_results:
            print(f"{Fore.YELLOW}No results to display.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Search Results ({len(self.current_results)} items):{Style.RESET_ALL}")
        
        for i, item in enumerate(self.current_results, 1):
            self._print_result_item(i, item)
        
        print()
    
    def _print_result_item(self, index: int, item: Dict[str, Any]):
        """Print a single result item."""
        # Number with padding
        num_str = f"{Fore.WHITE}{Back.BLUE} {index:2d} {Style.RESET_ALL}"
        
        if item['type'] == 'track':
            title = item['title']
            artist = item['artist']
            album = item['album']
            duration = item['duration']
            
            print(f"{num_str} {Fore.GREEN}{title}{Style.RESET_ALL}")
            print(f"     {Fore.CYAN}by {artist}{Style.RESET_ALL} • {Fore.BLUE}{album}{Style.RESET_ALL} • {Fore.YELLOW}{duration}{Style.RESET_ALL}")
        
        elif item['type'] == 'album':
            title = item['title']
            artist = item['artist']
            tracks = item['tracks']
            
            print(f"{num_str} {Fore.GREEN}{title}{Style.RESET_ALL}")
            print(f"     {Fore.CYAN}by {artist}{Style.RESET_ALL} • {Fore.YELLOW}{tracks} tracks{Style.RESET_ALL}")
        
        elif item['type'] == 'artist':
            name = item['name']
            albums = item['albums']
            fans = item['fans']
            
            print(f"{num_str} {Fore.GREEN}{name}{Style.RESET_ALL}")
            print(f"     {Fore.YELLOW}{albums} albums{Style.RESET_ALL} • {Fore.CYAN}{fans:,} fans{Style.RESET_ALL}")
    
    def _download_by_number(self, number: int) -> bool:
        """Download item by its number in results."""
        try:
            if not self.current_results:
                print(f"{Fore.RED}No search results available.{Style.RESET_ALL}")
                return True
            
            # Validate number
            if number < 1 or number > len(self.current_results):
                print(f"{Fore.RED}Invalid number. Choose 1-{len(self.current_results)}{Style.RESET_ALL}")
                return True
            
            item = self.current_results[number - 1]
            url = item.get('url', '')
            
            # Validate URL if validator is available
            if self.validator:
                try:
                    validated_url = self.validator.validate_url(url)
                except Exception:
                    validated_url = url  # Use original URL if validation fails
            else:
                validated_url = url
            
            item_name = item.get('title', item.get('name', 'Unknown'))
            print(f"{Fore.BLUE}Downloading: {item_name}{Style.RESET_ALL}")
            
            # Check safety if available
            try:
                from dmx.error_handler import SafetyChecker
                if not SafetyChecker.check_disk_space(Path(self.config.output_dir)):
                    print(f"{Fore.YELLOW}Warning: Low disk space{Style.RESET_ALL}")
            except Exception:
                pass  # Skip safety check if not available
            
            success = self.client.download(validated_url)
            if success:
                print(f"{Fore.GREEN}✓ Download completed successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Download failed{Style.RESET_ALL}")
                
        except Exception as e:
            context = ErrorContext(
                "download", 
                additional_info={'number': number, 'item': item if 'item' in locals() else None}
            )
            self.error_handler.handle_error(e, context)
        
        return True
    
    async def _view_artist_profile(self, number: int) -> bool:
        """View artist profile with top songs and albums."""
        try:
            if not self.current_results:
                print(f"{Fore.RED}No search results available.{Style.RESET_ALL}")
                return True
            
            # Validate number
            if number < 1 or number > len(self.current_results):
                print(f"{Fore.RED}Invalid number. Choose 1-{len(self.current_results)}{Style.RESET_ALL}")
                return True
            
            artist = self.current_results[number - 1]
            
            if artist['type'] != 'artist':
                print(f"{Fore.RED}Selected item is not an artist.{Style.RESET_ALL}")
                return True
            
            artist_id = artist['id']
            print(f"{Fore.BLUE}Loading artist profile for {artist['name']}...{Style.RESET_ALL}")
            
            # Get artist profile
            profile = self.client.get_artist_profile(str(artist_id))
            
            if not profile:
                print(f"{Fore.RED}Could not load artist profile.{Style.RESET_ALL}")
                return True
            
            # Store artist info and albums for download functionality
            self.current_artist_info = profile.get('artist', {})
            self.current_artist_albums = profile.get('albums', [])
            
            self._display_artist_profile(profile)
            
        except Exception as e:
            context = ErrorContext(
                "artist_profile", 
                additional_info={'number': number, 'artist': artist if 'artist' in locals() else None}
            )
            self.error_handler.handle_error(e, context)
        
        return True
    
    def _display_artist_profile(self, profile: Dict[str, Any]):
        """Display artist profile with top songs and all albums."""
        artist_info = profile.get('artist', {})
        top_tracks = profile.get('top_tracks', [])
        albums = profile.get('albums', [])
        
        # Artist header
        print(f"\n{Fore.CYAN}🎤 Artist Profile{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{artist_info.get('name', 'Unknown')}{Style.RESET_ALL}")
        print(f"     {Fore.YELLOW}{artist_info.get('albums', 0)} albums{Style.RESET_ALL} • {Fore.CYAN}{artist_info.get('fans', 0):,} fans{Style.RESET_ALL}")
        
        # Top tracks (display only, not downloadable from here)
        if top_tracks:
            print(f"\n{Fore.BLUE}🎵 Top Songs:{Style.RESET_ALL}")
            for i, track in enumerate(top_tracks[:5], 1):  # Show top 5
                print(f"     {Fore.GREEN}{track['title']}{Style.RESET_ALL}")
                print(f"     {Fore.BLUE}{track['album']}{Style.RESET_ALL} • {Fore.YELLOW}{track['duration']}{Style.RESET_ALL}")
        
        # All albums (downloadable)
        if albums:
            print(f"\n{Fore.BLUE}💿 Albums (Enter number to download):{Style.RESET_ALL}")
            self._display_artist_albums()
        
        print(f"\n{Fore.CYAN}Commands: [number] = download album | [1,3,5] = download multiple | all/* = download all | 'back' = return to artist search | 'l' = list albums{Style.RESET_ALL}")
        print()
    
    def _display_artist_albums(self):
        """Display all albums from current artist with download numbers."""
        if not self.current_artist_albums:
            print(f"{Fore.YELLOW}No albums to display.{Style.RESET_ALL}")
            return
        
        for i, album in enumerate(self.current_artist_albums, 1):
            # Number with padding  
            num_str = f"{Fore.WHITE}{Back.BLUE} {i:2d} {Style.RESET_ALL}"
            print(f"{num_str} {Fore.GREEN}{album['title']}{Style.RESET_ALL}")
            print(f"     {Fore.YELLOW}{album['tracks']} tracks{Style.RESET_ALL}")
        print()
    
    def _download_album_from_artist(self, number: int) -> bool:
        """Download album by number from artist profile view."""
        try:
            if not self.current_artist_albums:
                print(f"{Fore.RED}No albums available for download.{Style.RESET_ALL}")
                return True
            
            # Validate number
            if number < 1 or number > len(self.current_artist_albums):
                print(f"{Fore.RED}Invalid number. Choose 1-{len(self.current_artist_albums)}{Style.RESET_ALL}")
                return True
            
            album = self.current_artist_albums[number - 1]
            album_title = album.get('title', 'Unknown')
            album_url = album.get('url', '')
            
            # Validate URL if validator is available
            if self.validator:
                try:
                    validated_url = self.validator.validate_url(album_url)
                except Exception:
                    validated_url = album_url
            else:
                validated_url = album_url
            
            print(f"{Fore.BLUE}Downloading album: {album_title} ({album.get('tracks', 0)} tracks){Style.RESET_ALL}")
            
            # Check safety if available
            try:
                from dmx.error_handler import SafetyChecker
                from pathlib import Path
                if not SafetyChecker.check_disk_space(Path(self.config.output_dir)):
                    print(f"{Fore.YELLOW}Warning: Low disk space{Style.RESET_ALL}")
            except Exception:
                pass
            
            success = self.client.download(validated_url)
            if success:
                print(f"{Fore.GREEN}✓ Album download completed successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Album download failed{Style.RESET_ALL}")
        
        except Exception as e:
            context = ErrorContext(
                "album_download",
                additional_info={'number': number, 'album': album if 'album' in locals() else None}
            )
            self.error_handler.handle_error(e, context)
        
        return True
    
    def _parse_selection_input(self, user_input: str) -> Optional[List[int]]:
        """Parse selection input supporting various formats.
        
        Supports:
        - Single number: "3" -> [3]
        - Comma-separated: "1,3,5" -> [1,3,5]  
        - Ranges: "1-5" -> [1,2,3,4,5]
        - Mixed: "1,3-5,8" -> [1,3,4,5,8]
        - All: "all" or "*" -> [1,2,3,...,N]
        
        Returns None if input is not a selection format.
        """
        user_input = user_input.strip().lower()
        
        # Handle 'all' or '*' keywords
        if user_input in ['all', '*']:
            if self.current_artist_albums:
                return list(range(1, len(self.current_artist_albums) + 1))
            elif self.current_results:
                return list(range(1, len(self.current_results) + 1))
            else:
                return []
        
        # Check if it looks like a selection (contains only digits, commas, dashes)
        if not re.match(r'^[\d,\-\s]+$', user_input):
            return None
        
        try:
            indices = set()
            parts = user_input.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Handle range like "1-5"
                    range_parts = part.split('-', 1)
                    if len(range_parts) == 2:
                        start = int(range_parts[0].strip())
                        end = int(range_parts[1].strip())
                        if start <= end:
                            indices.update(range(start, end + 1))
                        else:
                            # Invalid range
                            return None
                    else:
                        # Invalid format
                        return None
                else:
                    # Single number
                    indices.add(int(part))
            
            return sorted(list(indices))
            
        except ValueError:
            # Not a valid selection format
            return None
    
    async def _download_by_numbers(self, numbers: List[int]) -> bool:
        """Download multiple items by their numbers in results."""
        try:
            if not self.current_results:
                print(f"{Fore.RED}No search results available.{Style.RESET_ALL}")
                return True
            
            # Validate all numbers first
            invalid_numbers = [n for n in numbers if n < 1 or n > len(self.current_results)]
            if invalid_numbers:
                print(f"{Fore.RED}Invalid numbers: {', '.join(map(str, invalid_numbers))}. Choose 1-{len(self.current_results)}{Style.RESET_ALL}")
                return True
            
            # Remove duplicates and sort
            numbers = sorted(list(set(numbers)))
            
            if len(numbers) == 1:
                # Single download - use existing method for compatibility
                return self._download_by_number(numbers[0])
            
            # Multiple downloads
            print(f"{Fore.CYAN}Starting batch download of {len(numbers)} items...{Style.RESET_ALL}")
            
            # Show confirmation for large batches
            if len(numbers) > 5:
                items_preview = [self.current_results[n-1].get('title', self.current_results[n-1].get('name', f'Item {n}')) for n in numbers[:3]]
                preview_text = ', '.join(items_preview)
                if len(numbers) > 3:
                    preview_text += f" and {len(numbers) - 3} more"
                
                print(f"{Fore.YELLOW}About to download: {preview_text}{Style.RESET_ALL}")
                confirm = input(f"{Fore.BLUE}Continue? (y/N): {Style.RESET_ALL}").strip().lower()
                if confirm not in ['y', 'yes']:
                    print(f"{Fore.YELLOW}Download cancelled.{Style.RESET_ALL}")
                    return True
            
            return await self._download_multiple_items(numbers, self.current_results)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Batch download cancelled by user.{Style.RESET_ALL}")
            return True
        except Exception as e:
            context = ErrorContext("batch_download", additional_info={'numbers': numbers})
            self.error_handler.handle_error(e, context)
            return True
    
    async def _download_albums_from_artist(self, numbers: List[int]) -> bool:
        """Download multiple albums from artist profile view."""
        try:
            if not self.current_artist_albums:
                print(f"{Fore.RED}No albums available for download.{Style.RESET_ALL}")
                return True
            
            # Validate all numbers first
            invalid_numbers = [n for n in numbers if n < 1 or n > len(self.current_artist_albums)]
            if invalid_numbers:
                print(f"{Fore.RED}Invalid numbers: {', '.join(map(str, invalid_numbers))}. Choose 1-{len(self.current_artist_albums)}{Style.RESET_ALL}")
                return True
            
            # Remove duplicates and sort
            numbers = sorted(list(set(numbers)))
            
            if len(numbers) == 1:
                # Single download - use existing method
                return self._download_album_from_artist(numbers[0])
            
            # Multiple downloads
            print(f"{Fore.CYAN}Starting batch download of {len(numbers)} albums...{Style.RESET_ALL}")
            
            # Show confirmation for large batches  
            if len(numbers) > 3:
                albums_preview = [self.current_artist_albums[n-1].get('title', f'Album {n}') for n in numbers[:3]]
                preview_text = ', '.join(albums_preview)
                if len(numbers) > 3:
                    preview_text += f" and {len(numbers) - 3} more"
                
                print(f"{Fore.YELLOW}About to download albums: {preview_text}{Style.RESET_ALL}")
                confirm = input(f"{Fore.BLUE}Continue? (y/N): {Style.RESET_ALL}").strip().lower()
                if confirm not in ['y', 'yes']:
                    print(f"{Fore.YELLOW}Download cancelled.{Style.RESET_ALL}")
                    return True
            
            return await self._download_multiple_items(numbers, self.current_artist_albums, is_artist_albums=True)
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Batch download cancelled by user.{Style.RESET_ALL}")
            return True
        except Exception as e:
            context = ErrorContext("batch_album_download", additional_info={'numbers': numbers})
            self.error_handler.handle_error(e, context)
            return True
    
    async def _download_multiple_items(self, numbers: List[int], items: List[Dict[str, Any]], is_artist_albums: bool = False) -> bool:
        """Download multiple items with progress tracking."""
        successful_downloads = []
        failed_downloads = []
        
        try:
            for i, number in enumerate(numbers, 1):
                try:
                    item = items[number - 1]
                    item_name = item.get('title', item.get('name', f'Item {number}'))
                    
                    # Progress indicator
                    print(f"{Fore.BLUE}[{i}/{len(numbers)}] Downloading: {item_name}{Style.RESET_ALL}")
                    
                    # Get URL and validate
                    url = item.get('url', '')
                    if self.validator:
                        try:
                            validated_url = self.validator.validate_url(url)
                        except Exception:
                            validated_url = url
                    else:
                        validated_url = url
                    
                    # Safety check
                    try:
                        from dmx.error_handler import SafetyChecker
                        from pathlib import Path
                        if not SafetyChecker.check_disk_space(Path(self.config.output_dir)):
                            print(f"{Fore.YELLOW}Warning: Low disk space{Style.RESET_ALL}")
                    except Exception:
                        pass
                    
                    # Download
                    success = self.client.download(validated_url)
                    
                    if success:
                        successful_downloads.append((number, item_name))
                        print(f"{Fore.GREEN}  ✓ Completed{Style.RESET_ALL}")
                    else:
                        failed_downloads.append((number, item_name))
                        print(f"{Fore.RED}  ✗ Failed{Style.RESET_ALL}")
                    
                    # Small delay between downloads to avoid overwhelming the service
                    if i < len(numbers):  # Don't delay after the last item
                        await asyncio.sleep(0.5)
                        
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Batch download cancelled by user.{Style.RESET_ALL}")
                    break
                except Exception as e:
                    item_name = f"Item {number}"
                    try:
                        item_name = items[number - 1].get('title', items[number - 1].get('name', item_name))
                    except:
                        pass
                    failed_downloads.append((number, item_name))
                    print(f"{Fore.RED}  ✗ Error downloading {item_name}: {str(e)}{Style.RESET_ALL}")
                    continue
            
            # Summary
            print(f"\n{Fore.CYAN}Batch Download Summary:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✓ Successful: {len(successful_downloads)}{Style.RESET_ALL}")
            if successful_downloads:
                for number, name in successful_downloads:
                    print(f"  {number}. {name}")
            
            if failed_downloads:
                print(f"{Fore.RED}✗ Failed: {len(failed_downloads)}{Style.RESET_ALL}")
                for number, name in failed_downloads:
                    print(f"  {number}. {name}")
            
            return True
            
        except Exception as e:
            context = ErrorContext("multi_download", additional_info={'numbers': numbers, 'is_artist_albums': is_artist_albums})
            self.error_handler.handle_error(e, context)
            return True
    
    def _get_mode_color(self):
        """Get color for current mode."""
        colors = {
            'tracks': Fore.GREEN,
            'albums': Fore.BLUE,
            'artists': Fore.MAGENTA
        }
        return colors.get(self.current_mode, Fore.WHITE)