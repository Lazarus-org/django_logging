## Unreleased (2024-09-05)

### 🚀 CI
- **ci**: Added automated build and release process. ([1a3bb2b](https://github.com/lazarus-org/django_logging/commit/1a3bb2b))
  - Added a GitHub Actions workflow for automated build and release.
  - Workflow triggers on new tags matching the `v*.*.*` pattern.
  - Includes steps to set up Python, install dependencies, and build the package using Poetry.
  - Automatically publishes the built package to PyPI using stored PyPI token secrets.
  - Ensures the release job only runs after the 'test' job passes successfully.

### ⚡️🔨📚 Refactor
- **docs**: Updated badges in README MarkDown file. ([c82f452](https://github.com/lazarus-org/django_logging/commit/c82f452))
  - Added pylint badge to display code quality rating in `README.md`.
  - Updated pre-commit badge color.

- **docs**: Updated badges and references in RST docs. ([c82f452](https://github.com/lazarus-org/django_logging/commit/c82f452))
  - Added pylint badge to the documentation.
  - Updated the settings section in various `.rst` files to reflect recent changes.
  - Enhanced documentation for better readability and accuracy.

## v1.0.3 (2024-09-05)
### ✨ Added
- **chore(pyproject)**: Added `python-semantic-release` configuration to automate versioning and releases. (`945c648`)
- **docs**: Added pre-commit badge to display status in documentation. (`f40a9e5`, `7fca7b7`)

### 🛠️ Changed
- **docs**: Updated badge URLs and paths in documentation for correct references. (`f40a9e5`, `7fca7b7`)

### 🐛 Fixed
- **pyproject**: Updated dependencies and development requirements in the `pyproject.toml` configuration. (`945c648`)

### 🔀 Merged
- **Merge PR #77**: Merged the `chore/pyproject-config` branch into the main branch. (`c2ebad3`)

## v1.0.2 (2024-09-02)
**Added**
- tag_format in commitizen configuration in pyproject.toml
- changelog path in poetry urls
- Add FUNDING.yml file

**Refactored**
- Renamed setup_django into settings_configuration in tests dir
- Moved settings_configuration from fixtures into tests root dir


## v1.0.1 (2024-09-02)
**Refactored**
- Updated badges path in README.md and installation guide
- Updated badges path in index.rst and installation guide
- Updated headers in RestructuredText documentations

**Fixed**
- Removed repository from tool.poetry
- Fixed read the docs path in poetry urls

## v1.0.0 (2024-09-02)
- initial Release
