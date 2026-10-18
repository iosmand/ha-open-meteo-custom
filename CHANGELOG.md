# Changelog

Releases are published automatically when the `version` in
`custom_components/open_meteo_custom/manifest.json` changes on `main`.
The section below matching the new version is used as the release notes.

## v1.0.11

### 🔧 Dependency Updates
- Bump `openmeteo-sdk` from 1.27.2 to 1.28.0 (PR #11)
- Update `aiohttp` requirement from >=3.14.1 to >=3.14.4 (PR #13)
- Update `yarl` requirement from >=1.24.2 to >=1.25.1 (PR #12)
- Bump `actions/setup-python` from 6 to 7 (PR #9)

### 🛠️ Code Quality (PR #14)
- Removed the duplicate `.coordinator` import in `sensor.py`
- Moved misplaced and function-level imports to the top of their modules (`coordinator.py`, `weather.py`, tests)
- Removed unused imports and placeholder-less f-strings
- Fixed `tests/test_locations.py` running the live API checks twice
- Added a `ruff` lint job to the validation workflow

### 🚀 Release Automation
- New `Release` workflow publishes a GitHub release whenever the manifest version changes on `main`
