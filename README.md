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
- [Development](#development)
- [License](#license)
- [Contributing](#contributing)

## Features
- **Recursive Scanning**: Organizes files in nested subdirectories
- **Smart Categorization**: 6 built-in categories (Images, Videos, Documents, Audio, Archives, Others)
- **Safe Operations**: Never overwrites files; adds counter suffix for conflicts
- **Dry-run Mode**: Preview all changes before executing
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
| `-e`, `--exclude` | Additional glob patterns to exclude | `*.git`, `*/venv`, etc. |
| `-n`, `--dry-run` | Show what would happen without moving files | `False` |
| `-v`, `--verbose` | Increase output verbosity (can be repeated) | `0` |
| `-o`, `--output` | Base directory for output (defaults to first source path) | `None` |
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

## Support
If you encounter any issues or have feature requests, please [open an issue](https://github.com/vlrntid/file-organizer/issues).