# dmx-music v0.1.0 Release Notes

## 🎉 New Features

### 🎵 Complete Artist Browsing Experience
- **Artist Profiles**: View detailed artist information with fan counts and album statistics
- **Top Songs Display**: See artist's most popular tracks with album names and durations  
- **Complete Album Collections**: Browse ALL albums from any artist (not just recent ones)
- **Smart Artist Sorting**: Artists automatically sorted by fan count (most popular first)

### 💿 Direct Album Downloads  
- **One-Click Album Downloads**: Select any album by number and download instantly
- **Clear Visual Interface**: Albums numbered and clearly marked as downloadable
- **Navigation Support**: `back` command to return from artist profile to search results
- **Context-Aware Prompts**: Shows current context (e.g., `[Pez Albums] >`)

### 🎯 Enhanced User Experience
- **Intuitive Workflow**: Search artists → View profile → Browse albums → Download
- **No Confusion**: Top songs display-only (no numbers), albums numbered for download
- **Dynamic Commands**: `l` lists albums, `back` navigates up, numbers download albums
- **Progress Feedback**: Clear indication of what's happening during downloads

## 🔧 Technical Improvements

### Package Distribution
- **PyPI Ready**: Now available as `dmx-music` on PyPI for easy `pip install`
- **Dual Commands**: Both `dmx` and `dmx-music` commands work after installation
- **Better Dependencies**: Properly specified minimum versions for all dependencies
- **Cross-Platform**: Full Windows, macOS, and Linux support

### Performance & Reliability
- **Efficient API Calls**: Optimized album metadata fetching with proper track counts
- **Better Error Handling**: Graceful fallbacks for API failures
- **Memory Efficient**: Streams large album lists without memory issues
- **Caching Support**: Reduces redundant API calls for better performance

## 🚀 Installation

### For End Users
```bash
# Install from PyPI (recommended)
pip install dmx-music

# Run the application
dmx
```

### For Developers
```bash
# Clone and install in development mode
git clone https://github.com/cargaona/dmx.git
cd dmx
pip install -e .
```

## 📖 Usage Example

```bash
# Start dmx
dmx

# Switch to artists mode  
[tracks] > m artists

# Search for artists (automatically sorted by fans)
[artists] > radiohead

# Results show most popular first:
# 1. Radiohead - 2,847,291 fans (25 albums)
# 2. Radio Head - 1,234 fans (3 albums)

# View profile for main Radiohead
[artists] > 1

# Browse all 25 albums
[Radiohead Albums] > l

# Download any album
[Radiohead Albums] > 3  # Download "OK Computer"

# Go back to artist search
[Radiohead Albums] > back
```

## 🐛 Bug Fixes

- Fixed album track counts showing as 0 in artist profiles
- Corrected artist search returning track results instead of artist results  
- Improved error handling for failed API requests
- Fixed navigation state not clearing properly between searches

## 📋 Full Command Reference

### Search Modes
- `m tracks` / `m albums` / `m artists` - Switch search mode
- `s <query>` - Search tracks
- `sa <query>` - Search albums  
- `st <query>` - Search artists

### Artist Profile Navigation
- `[number]` - In artist mode: view profile; in profile: download album
- `back` / `b` - Return from artist profile to search results
- `l` - List current results or albums

### General Commands
- `status` - Show system status
- `h` - Show help
- `q` - Quit

## 🔜 Coming Soon

- Playlist browsing and management
- Track-level downloads from artist profiles
- Search history and favorites
- Batch album downloads
- Export/import functionality

---

**Package**: `dmx-music` v0.1.0  
**Python**: 3.8+ required  
**License**: MIT  
**Dependencies**: deemix, click, colorama, requests, aiohttp