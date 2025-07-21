# Building and Publishing dmx-music to PyPI

## Prerequisites

```bash
# Install build tools
pip install build twine

# Make sure you have PyPI account and API token
```

## Building the Package

```bash
# Clean any existing builds
rm -rf dist/ build/ *.egg-info/

# Build source distribution and wheel
python -m build

# This creates:
# dist/dmx-music-0.1.0.tar.gz
# dist/dmx_music-0.1.0-py3-none-any.whl
```

## Testing the Package Locally

```bash
# Install in development mode
pip install -e .

# Or install from built wheel
pip install dist/dmx_music-0.1.0-py3-none-any.whl

# Test the installation
dmx --help
dmx-music --help
```

## Publishing to PyPI

### Test PyPI (Recommended first)

```bash
# Upload to test PyPI
twine upload --repository testpypi dist/*

# Test installation from test PyPI
pip install --index-url https://test.pypi.org/simple/ dmx-music
```

### Production PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Anyone can now install with:
pip install dmx-music
```

## Version Management

Update version in `pyproject.toml`:

```toml
[project]
name = "dmx-music"
version = "0.1.1"  # Increment as needed
```

## Package Information

- **Package name**: `dmx-music` (to avoid conflicts with existing `dmx` package)
- **Import name**: `dmx` (users still import with `import dmx`)
- **Commands**: `dmx` and `dmx-music` (both work)
- **Python**: >=3.8
- **Dependencies**: deemix, click, colorama, requests, aiohttp

## User Installation

After publishing, users can install with:

```bash
pip install dmx-music
```

And run with either:
```bash
dmx
# or
dmx-music
```