# PyPI Publishing Guide for dmx-music

## 🚀 Automated Publishing with GitHub Actions

This project is set up for automatic PyPI publishing when you create a GitHub release.

### Prerequisites

1. **PyPI Account**: Create accounts on both PyPI and Test PyPI
   - PyPI: https://pypi.org/account/register/
   - Test PyPI: https://test.pypi.org/account/register/

2. **API Tokens**: Generate API tokens for both platforms
   - PyPI: https://pypi.org/manage/account/#api-tokens
   - Test PyPI: https://test.pypi.org/manage/account/#api-tokens

3. **GitHub Secrets**: Add tokens to your repository secrets
   - Go to: `Settings > Secrets and variables > Actions`
   - Add secrets:
     - `PYPI_API_TOKEN`: Your PyPI token  
     - `TEST_PYPI_API_TOKEN`: Your Test PyPI token

### How to Publish

#### Method 1: Create a GitHub Release (Recommended)

1. **Update version** in `pyproject.toml` if needed:
   ```toml
   version = "0.1.1"  # or next version
   ```

2. **Create a release** on GitHub:
   - Go to your repository → Releases → Create a new release
   - Tag: `v0.1.0` (or appropriate version)
   - Title: `dmx-music v0.1.0`
   - Description: Copy from `RELEASE_NOTES.md`
   - Click "Publish release"

3. **Automatic publication**:
   - GitHub Actions will automatically build and publish to PyPI
   - Check the "Actions" tab to monitor progress

#### Method 2: Manual Test (Test PyPI only)

1. Go to Actions tab in your repository
2. Click "Publish to PyPI" workflow
3. Click "Run workflow" 
4. This will publish to Test PyPI only

### Workflow Details

The automated workflow (`/.github/workflows/publish.yml`) will:

1. ✅ Build the package (`python -m build`)
2. ✅ Run quality checks (`twine check`)  
3. ✅ Publish to PyPI when you create a release
4. ✅ Publish to Test PyPI when manually triggered

### Version Management Strategy

For semantic versioning:

- **0.1.0**: Initial release with core features
- **0.1.x**: Bug fixes and small improvements  
- **0.2.0**: New features (like playlist support)
- **1.0.0**: Stable API, production ready

### Testing Your Release

After publishing to Test PyPI:

```bash
# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ dmx-music

# Test the installation
dmx --help
dmx-music --help
```

After publishing to PyPI:

```bash
# Install from PyPI  
pip install dmx-music

# Verify it works
dmx
```

### Manual Publishing (If Needed)

If you prefer manual control:

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Troubleshooting

**Common Issues:**

1. **"File already exists"**: You're trying to upload the same version twice
   - Solution: Increment version in `pyproject.toml`

2. **"Invalid token"**: API token is incorrect or expired
   - Solution: Regenerate token and update GitHub secrets

3. **"Missing dependencies"**: Build fails due to missing dependencies
   - Solution: Check that all dependencies are listed in `pyproject.toml`

**Workflow Status:**

- ✅ Green checkmark: Successfully published
- ❌ Red X: Failed (check logs in Actions tab)
- 🟡 Yellow dot: In progress

### Security Notes

- Never commit API tokens to your repository
- Use GitHub Secrets for all sensitive information  
- Tokens are scoped to your account only
- Revoke and regenerate tokens if compromised

### Next Steps After Publishing

1. **Update documentation** with new installation instructions
2. **Announce release** in relevant communities  
3. **Monitor issues** and user feedback
4. **Plan next version** features and improvements

---

**Current Version**: v0.1.0  
**Package Name**: `dmx-music`  
**Installation**: `pip install dmx-music`