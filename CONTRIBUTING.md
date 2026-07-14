# Contributing to neatfiles

Thanks for your interest in contributing! 🎉

## Getting started

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dev dependencies:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate   # Windows (Git Bash)
   pip install -e ".[dev]"
   ```
3. Create a feature branch off `main`:
   ```bash
   git checkout -b feature/your-feature
   ```

## Development workflow

- Write clean, readable code and add comments for any non-obvious logic.
- Add or update tests under `tests/`.
- Keep `CHANGELOG.md` up to date (add an entry under `## [Unreleased]`).
- Run the checks before committing:
  ```bash
  ruff check .
  ruff format .
  mypy .
  pytest
  ```

## Pull requests

- `main` is a **protected branch** — all changes must go through a pull request.
- Fill in the PR template and make sure CI is green.
- Reference any related issue (e.g. `Closes #123`).

## Releasing

Maintainers:

1. Update `CHANGELOG.md` (move `[Unreleased]` → a new version heading with the date).
2. Bump `version` in `pyproject.toml`.
3. Tag and push:
   ```bash
   git tag -a v0.2.0 -m "neatfiles v0.2.0"
   git push origin v0.2.0
   ```
4. The **Publish to PyPI** workflow builds and uploads to PyPI automatically
   (requires the `PYPI_API_TOKEN` repository secret).
