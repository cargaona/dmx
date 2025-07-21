# Release Checklist for dmx-music

Use this checklist when preparing a new release.

## Pre-Release Setup (One-time)

- [ ] Create PyPI account at https://pypi.org/account/register/
- [ ] Create Test PyPI account at https://test.pypi.org/account/register/  
- [ ] Generate PyPI API token at https://pypi.org/manage/account/#api-tokens
- [ ] Generate Test PyPI API token at https://test.pypi.org/manage/account/#api-tokens
- [ ] Add `PYPI_API_TOKEN` to GitHub repository secrets
- [ ] Add `TEST_PYPI_API_TOKEN` to GitHub repository secrets

## For Each Release

### 1. Prepare Release
- [ ] Update version in `pyproject.toml`
  ```toml
  version = "0.1.x"  # Increment appropriately
  ```
- [ ] Update `RELEASE_NOTES.md` with new features and changes
- [ ] Test the package locally:
  ```bash
  pip install -e .
  dmx --help  # Should work
  ```
- [ ] Commit all changes to main/master branch

### 2. Create GitHub Release
- [ ] Go to repository → Releases → "Create a new release"
- [ ] Tag version: `v0.1.x` (matching pyproject.toml)
- [ ] Release title: `dmx-music v0.1.x`
- [ ] Description: Copy relevant sections from `RELEASE_NOTES.md`
- [ ] Click "Publish release"

### 3. Monitor Automated Publishing
- [ ] Go to Actions tab in GitHub
- [ ] Watch "Publish to PyPI" workflow
- [ ] Verify it completes successfully (green checkmark)
- [ ] Check https://pypi.org/project/dmx-music/ for new version

### 4. Verify Publication
- [ ] Test installation from PyPI:
  ```bash
  pip install dmx-music==0.1.x
  dmx --help
  dmx-music --help
  ```
- [ ] Test basic functionality:
  ```bash
  dmx  # Should start interactive mode
  # Try: m artists, search for artist, etc.
  ```

### 5. Post-Release
- [ ] Update README.md if needed with any installation changes
- [ ] Announce release (if desired)
- [ ] Plan next version features

## Manual Testing (Optional)

If you want to test on Test PyPI first:

- [ ] Go to Actions → "Publish to PyPI" → "Run workflow" → Run
- [ ] This publishes to Test PyPI only
- [ ] Test install: `pip install --index-url https://test.pypi.org/simple/ dmx-music`
- [ ] If successful, proceed with GitHub release for production PyPI

## Version Strategy

- **0.1.x**: Initial releases, bug fixes, small improvements
- **0.2.x**: New major features (playlist support, etc.)
- **0.x.x**: API changes, significant new functionality  
- **1.0.0**: Stable API, production ready

## Quick Commands

```bash
# Check current version
grep version pyproject.toml

# Test local build
python -m build

# Check package quality
twine check dist/*

# View recent releases
gh release list  # if you have GitHub CLI
```