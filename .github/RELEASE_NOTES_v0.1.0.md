# file-organizer v0.1.0

The first release of **file-organizer** — a safe, preview-first command-line
tool that automatically sorts files into categorized folders.

## Highlights
- 🗂️ Six built-in categories: **Images, Videos, Documents, Audio, Archives, Others**
- 🔍 Recursive directory scanning with customizable exclude patterns
- 👀 **Dry-run mode** — preview every move before touching anything
- 🛡️ **Conflict-safe moves** — existing files are never overwritten (a numeric suffix is added)
- 🕒 Move history saved to `~/.file_organizer_history.json` for future undo support
- 💻 Cross-platform: Windows, macOS, and Linux

## Install
```bash
pip install file-organizer
```
Or clone and install in development mode:
```bash
pip install -e ".[dev]"
```

## Quick start
```bash
file-organizer ~/Downloads --dry-run   # preview the moves
file-organizer ~/Downloads -o ~/Sorted # organize into ~/Sorted
```

## Quality
- ✅ 31 passing tests (`pytest`)
- ✅ `ruff` clean (lint + format)
- ✅ `mypy` clean (full type hints)
- ✅ GitHub Actions CI (lint, format, type-check, test, coverage)

See [CHANGELOG.md](CHANGELOG.md) for the full list of changes.
