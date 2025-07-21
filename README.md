# dmx

Simple music search and download tool using deemix.

## Features

- **Interactive Search**: Search for tracks, albums, and artists on Deezer
- **Quality Downloads**: Automatic quality fallback (320kbps → 128kbps)
- **Smart Detection**: Avoids re-downloading existing files
- **Clean Interface**: Minimal, colorful command-line interface
- **ARL Authentication**: Secure authentication using Deezer ARL tokens

## Installation

### Using Nix (Recommended)

```bash
# Install directly from GitHub
nix run github:cargaona/dmx

# Or add to your flake inputs
{
  inputs.dmx.url = "github:cargaona/dmx";
}
```

### Using pip

```bash
pip install dmx
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

### Album Downloads
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