# dmx - Interactive Music Search & Download

Interactive music search and download tool with Deezer integration. Browse artists, view their profiles, and download albums directly from the command line.

## ✨ Features

### 🎵 **Advanced Artist Browsing**
- **Artist Search & Profiles**: Search artists and view detailed profiles with top songs
- **Complete Album Collections**: Browse ALL albums from any artist (sorted by popularity)  
- **Direct Album Downloads**: Download any album by simply typing its number
- **Smart Sorting**: Artists sorted by fan count for better discovery

### 🎯 **Interactive Experience**
- **Multi-Mode Search**: Switch between tracks, albums, and artists instantly
- **Audio Previews**: 30-second track previews with playback controls
- **Multiple Downloads**: Select multiple items with ranges like `[1,3-5,8]`
- **Intuitive Navigation**: Browse artist profiles with `back` command support
- **Visual Feedback**: Color-coded interface with progress indicators
- **Smart Detection**: Avoids re-downloading existing files

### ⚡ **Quality & Performance**
- **Quality Downloads**: Automatic quality fallback (320kbps → 128kbps → available)
- **Batch Operations**: Efficient album downloads with progress tracking
- **ARL Authentication**: Secure authentication using Deezer ARL tokens
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📦 Installation

### Using pip (Recommended)

```bash
pip install dmx-music
```

### Using Nix

```bash
# Install directly from GitHub
nix run github:cargaona/dmx

# Or add to your flake inputs
{
  inputs.dmx.url = "github:cargaona/dmx";
}
```

### From source

```bash
git clone https://github.com/cargaona/dmx.git
cd dmx
pip install -e .
```

## Quick Start

1. **Get your ARL token** from Deezer (check browser cookies)

2. **Configure dmx**:
   ```bash
   dmx config set arl YOUR_ARL_TOKEN_HERE
   dmx config set quality 320
   dmx config set output ~/Music
   ```

3. **Start interactive mode**:
   ```bash
   dmx
   ```

4. **Search and download**:
   ```
   [tracks] > lady gaga disease
   [tracks] > 1  # Download first result
   ```

## 🎨 Artist Browsing Workflow

**Featured in v0.1.0**: Complete artist profile browsing with album downloads

```bash
# Switch to artists mode
[tracks] > m artists

# Search for artists (sorted by fan count)
[artists] > pez

# View artist profile
[artists] > 2  # Select Pez with 10,580 fans

# Browse ALL artist albums (72 total)
[Pez Albums] > l  # List all albums

# Download any album directly  
[Pez Albums] > 15  # Download album #15

# Navigate back
[Pez Albums] > back
[artists] > 
```

### Example Artist Profile:
```
🎤 Artist Profile
Pez
     72 albums • 10,580 fans

🎵 Top Songs:
     Aire al Fin
     El Manto Eléctrico • 3:13

💿 Albums (Enter number to download):
  1  Goodbye Dear, Ok Chicago. (11 tracks)
  2  Ion (13 tracks)
  [... 70 more albums ...]

Commands: [number] = download album | [1,3,5] = download multiple | t<number> = preview top track | 'back' = return to artist search
```

## Usage

### Interactive Mode (Default)

```bash
dmx
```

Commands available in interactive mode:
- `<query>` - Search for tracks
- `sa <query>` - Search albums  
- `st <query>` - Search artists
- `<number>` - Download by number
- `[1,3-5,8]` - Download multiple items/ranges
- `all` or `*` - Download all current results
- `p <number>` - Play 30-second preview of track
- `t<number>` - Play preview of artist's top track
- `play` - Play/pause current preview
- `stop` - Stop current preview
- `m tracks|albums|artists` - Switch mode
- `l` - List current results
- `status` - Show system status
- `q` - Quit

### Direct Commands

```bash
# Search
dmx search "artist song"
dmx search -a "album name"
dmx search -t "artist name"

# Download by URL
dmx download "https://www.deezer.com/track/123456"
dmx download "https://www.deezer.com/album/123456"

# Configuration
dmx config list
dmx config set quality 320
dmx config set output ~/Music

# System status
dmx status
```

## Configuration

Configuration is stored in `~/.config/dmx/config.json`.

### Available Settings

- `arl` - Your Deezer ARL token (required for downloads)
- `quality` - Audio quality: `128`, `320`, or `FLAC`
- `output` - Download directory (default: `~/Downloads/Music`)

### Getting ARL Token

1. Open Deezer in your browser
2. Log in to your account
3. Open Developer Tools (F12)
4. Go to Application/Storage → Cookies
5. Find the `arl` cookie value
6. Copy the value and use it with `dmx config set arl YOUR_TOKEN`

**Note**: You need a Deezer Premium subscription for high-quality downloads.

## Examples

### Search and Download
```bash
# Interactive search
dmx

# Search for a specific song
[tracks] > bruno mars finesse
1  Finesse (Remix; feat. Cardi B)
   by Bruno Mars • Finesse (feat. Cardi B) (Remix) • 3:37

# Download it
[tracks] > 1
✓ Downloaded: Bruno Mars - Finesse (Remix; feat. Cardi B).mp3
```

### Album Downloads & Multiple Selection
```bash
# Switch to album mode
[tracks] > m albums

# Search for album
[albums] > lady gaga mayhem
1  MAYHEM
   by Lady Gaga • 14 tracks

# Download entire album
[albums] > 1
✓ Downloaded 14 files

# Download multiple items (also works with tracks/artists)
[tracks] > [1,3-5,8]  # Downloads items 1, 3, 4, 5, and 8
[tracks] > all        # Downloads all current results
```

### Audio Previews
```bash
# Play 30-second preview of a track
[tracks] > p 1
🎵 Playing preview: Song Title by Artist
Preview started. Use 'play' to pause/resume, 'stop' to stop.

# Control playback
[tracks] > play       # Pause/resume
[tracks] > stop       # Stop preview

# Preview artist's top tracks (in artist profile)
[Artist Albums] > t1  # Preview first top track
[Artist Albums] > t2  # Preview second top track
```

### Direct URL Downloads
```bash
# Download specific track
dmx download "https://www.deezer.com/track/123456"

# Download entire album
dmx download "https://www.deezer.com/album/123456"
```

## File Organization

Downloaded files are organized as:
```
~/Downloads/Music/
├── Artist - Album/
│   ├── 01 - Track Name.mp3
│   ├── 02 - Another Track.mp3
│   └── ...
└── Artist - Single Track.mp3
```

## Requirements

- Python 3.8+
- Valid Deezer ARL token
- Internet connection
- Optional: pygame (for audio previews) - `pip install pygame`

## Development

### Using Nix

```bash
# Enter development shell
nix develop

# Install in development mode
python -m pip install -e .

# Run tests
pytest
```

### Manual Setup

```bash
# Clone repository
git clone https://github.com/cargaona/dmx.git
cd dmx

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\\Scripts\\activate  # Windows

# Install dependencies
pip install -e .

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- Built on [deemix](https://deemix.app) - the core download engine
- Uses [Deezer](https://deezer.com) for music metadata and streaming