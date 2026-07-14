# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0]

### Added
- Initial release of the `file-organizer` CLI tool
- Six built-in categories: Images, Videos, Documents, Audio, Archives, Others
- Recursive directory scanning with customizable exclude patterns
- Dry-run mode that previews every planned move before any change is made
- Conflict-safe moves: existing files are never overwritten; a numeric suffix is appended
- Move history recorded to `~/.file_organizer_history.json` for future undo support
- Cross-platform support (Windows, macOS, Linux)
- Full test suite with `pytest`
- Continuous integration via GitHub Actions (lint, format, type-check, test, coverage)

### Changed
- Extension lookup refactored to an O(1) dictionary for fast categorization

### Fixed
- Graceful handling of `PermissionError` and `OSError` during moves instead of crashing
