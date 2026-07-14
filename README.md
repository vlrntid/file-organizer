# File Organizer

[![CI](https://github.com/vlrntid/file-organizer/actions/workflows/ci.yml/badge.svg)](https://github.com/vlrntid/file-organizer/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/vlrntid/file-organizer/branch/main/graph/badge.svg)](https://codecov.io/gh/vlrntid/file-organizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org)

A command-line tool to automatically organize files into categorized folders (Images, Videos, Documents, Audio, Archives, Others).

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Demo](#demo)
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)

## Features
- **Recursive Scanning**: Organizes files in nested subdirectories
- **Smart Categorization**: 6 built-in categories (Images, Videos, Documents, Audio, Archives, Others)
- **Date Organization**: Alternatively group files into `year/month` folders with `--by-date`
- **Duplicate Detection**: Route identical files to a `Duplicates` folder with `--dedupe`
- **Safe Operations**: Never overwrites files; adds counter suffix for conflicts
- **Dry-run Mode**: Preview all changes before executing
- **Undo**: Reverse the last organization using the recorded move history
- **JSON Report**: Emit a machine-readable report of every move with `--report`
- **Quiet Mode**: Suppress the preview for cron/automation with `-q`
- **Safe by Default**: Prompts for confirmation before moving (skip with `-y`)
- **Flexible Exclusions**: Customizable ignore patterns for git repos, virtual environments, etc.
- **Multiple Sources**: Organize from multiple directories into one target
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation
```bash
# Clone the repository
git clone https://github.com/vlrntid/file-organizer.git

# Install in development mode
pip install -e ".[dev]"

# Or install from PyPI (when published)
pip install file-organizer
```

## Usage
```bash
# Basic usage
file-organizer /path/to/source

# Dry run to see what would happen
file-organizer /path/to/source --dry-run

# Undo the last organization
file-organizer --undo

# Write a JSON report of the planned moves
file-organizer ~/Downloads --dry-run --report plan.json

# Quiet mode (summary only) for cron/automation
file-organizer ~/Downloads -q

# Organize into year/month folders by modification date
file-organizer ~/Downloads --by-date

# Route content-duplicate files into a Duplicates folder
file-organizer ~/Downloads --dedupe

# Verbose output
file-organizer /path/to/source -v

# Custom output directory
file-organizer /path/to/source -o /path/to/organize

# Multiple source directories
file-organizer /path/to/source1 /path/to/source2

# Custom exclude patterns
file-organizer /path/to/source --exclude "*cache*" --exclude "*.tmp"
```

### Arguments Reference
| Argument | Description | Default |
|----------|-------------|---------|
| `PATH` | One or more source directories to scan | Required |
| `-e`, `--exclude` | Additional glob patterns to exclude | `*/.git`, `*/venv`, etc. |
| `-n`, `--dry-run` | Show what would happen without moving files | `False` |
| `-v`, `--verbose` | Increase output verbosity (can be repeated) | `0` |
| `-o`, `--output` | Base directory for output (defaults to first source path) | `None` |
| `--undo` | Reverse the last organization using the move history | `False` |
| `-q`, `--quiet` | Suppress the preview; only print the final summary | `False` |
| `--report` | Write a JSON report of the planned/applied moves to this file | `None` |
| `--by-date` | Organize files into `year/month` folders by modification time | `False` |
| `--dedupe` | Route content-duplicate files to a `Duplicates` folder | `False` |
| `-y`, `--yes` | Skip the interactive confirmation prompt before moving | `False` |
| `--version` | Show program version and exit | `N/A` |

## Configuration
The tool uses sensible defaults but can be customized via command-line arguments:

### Default Exclude Patterns
```python
DEFAULT_EXCLUDE = [
    ".*",               # hidden files/folders
    "*/.git",           # git repos
    "*/.hg",            # mercurial repos
    "*/.svn",           # subversion repos
    "*/venv", "*/env", "*/virtualenv",  # virtual environments
    "*/node_modules",  # Node.js projects
]
```

### File Categories
Built-in categories with common extensions:

- **Images**: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp, .svg, .ico, .heic, .raw, .cr2, .nef, .arw, .dng, .psd, .ai, .eps
- **Videos**: .mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v, .mpg, .mpeg, .3gp, .ts, .mts, .m2ts, .vob, .ogv, .rm, .rmvb, .asf, .divx, .xvid
- **Documents**: .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx, .csv, .md, .tex, .epub, .mobi, .azw, .pages, .numbers, .key, .odp, .ods, .odg, .odf, .wpd, .wps, .xml, .json, .yaml, .yml, .toml, .ini, .cfg, .conf, .log
- **Audio**: .mp3, .wav, .flac, .aac, .ogg, .m4a, .wma, .opus, .aiff, .aif, .au, .ra, .ram, .mid, .midi, .amr, .ape, .alac, .dts, .ac3, .mp2, .mpa
- **Archives**: .zip, .rar, .7z, .tar, .gz, .bz2, .xz, .tgz, .tbz2, .txz, .zst, .lz4, .lz, .lzo, .rz, .sz, .cab, .iso, .img, .dmg, .pkg, .deb, .rpm, .msi, .apk, .ipa, .jar, .war, .ear
- **Others**: Any extension not in the above lists

## Examples

### Example 1: Organize Downloads Folder
```bash
file-organizer ~/Downloads -o ~/Organized
```

### Example 2: Dry-run with Verbose Output
```bash
file-organizer ~/Downloads --dry-run -v
```

### Example 3: Organize Multiple Project Directories
```bash
file-organizer ~/Projects/project1 ~/Projects/project2 -o ~/AllAssets
```

### Example 4: Exclude Cache Directories
```bash
file-organizer ~/Project --exclude "*cache*" --exclude "__pycache__"
```

## Demo

Preview changes before touching anything with `--dry-run`:

```text
$ file-organizer ~/Downloads --dry-run

============================================================
📦 Preview: 5 files will be moved
============================================================

📁 Downloads/Archives
   📄 backup.zip  →  backup.zip

📁 Downloads/Audio
   📄 song.mp3  →  song.mp3

📁 Downloads/Documents
   📄 notes.txt  →  notes.txt
   📄 report.pdf  →  report.pdf

📁 Downloads/Images
   📄 photo.jpg  →  photo.jpg

============================================================
INFO: 🧪 Dry-run complete – no changes were applied.
```

Then run for real (or with `--undo` afterwards to reverse it):

```text
$ file-organizer ~/Downloads
✅ 5 files moved, 0 failures.
```

## Development

### Setup
```bash
git clone https://github.com/vlrntid/file-organizer.git
cd file-organizer
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=file_organizer --cov-report=html

# Run specific test file
pytest tests/test_file_organizer.py -v
```

### Code Quality
```bash
# Lint with ruff
ruff check .

# Format with ruff
ruff format .

# Type check with mypy
mypy .
```

### CI & Coverage
Linting, type-checking, and tests run automatically on every push/PR via
GitHub Actions (see `.github/workflows/ci.yml`). Coverage is uploaded to
[Codecov](https://codecov.io); add a `CODECOV_TOKEN` repository secret (Settings →
Secrets) so coverage reporting works end to end.

### Building Distribution
```bash
python -m build
```

## License
Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Contributing
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add: AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

> **Note:** `main` is a protected branch — changes must be made via pull
> request and force-pushes are disabled. Branch from `main` and open a PR.

## Support
If you encounter any issues or have feature requests, please [open an issue](https://github.com/vlrntid/file-organizer/issues).