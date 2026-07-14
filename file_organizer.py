#!/usr/bin/env python3
"""
file_organizer.py – CLI tool to automatically organize files by type.

Features
--------
* Scans one or more source directories recursively
* Categorizes files into Images, Videos, Documents, Audio, Archives, Others
* Shows a preview of every move before any changes are made
* Never overwrites an existing file – adds a numeric suffix if needed
* Supports a dry‑run mode, custom exclude patterns and verbosity levels
* Fully typed, logged and tested‑ready (Python 3.10+)

Install with:
    pip install .
"""

# ----------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------
import argparse
import fnmatch
import logging
from datetime import datetime
import shutil
import sys
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple, cast

# ----------------------------------------------------------------------
# Logging configuration (JSON‑friendly, can be silenced with --quiet)
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration – Mapping of extensions → category
# ----------------------------------------------------------------------
FILE_CATEGORIES: Dict[str, List[str]] = {
    "Images": [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
        ".ico",
        ".heic",
        ".heif",
        ".raw",
        ".cr2",
        ".nef",
        ".arw",
        ".dng",
        ".psd",
        ".ai",
        ".eps",
    ],
    "Videos": [
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".3gp",
        ".3g2",
        ".ts",
        ".mts",
        ".m2ts",
        ".vob",
        ".ogv",
        ".rm",
        ".rmvb",
        ".asf",
        ".divx",
        ".xvid",
    ],
    "Documents": [
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".rtf",
        ".odt",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".csv",
        ".md",
        ".tex",
        ".epub",
        ".mobi",
        ".azw",
        ".pages",
        ".numbers",
        ".key",
        ".odp",
        ".ods",
        ".odg",
        ".odf",
        ".wpd",
        ".wps",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".log",
    ],
    "Audio": [
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
        ".wma",
        ".opus",
        ".aiff",
        ".aif",
        ".au",
        ".ra",
        ".ram",
        ".mid",
        ".midi",
        ".amr",
        ".ape",
        ".alac",
        ".dts",
        ".ac3",
        ".mp2",
        ".mpa",
    ],
    "Archives": [
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tgz",
        ".tbz2",
        ".txz",
        ".zst",
        ".lz4",
        ".lz",
        ".lzo",
        ".rz",
        ".sz",
        ".cab",
        ".iso",
        ".img",
        ".dmg",
        ".pkg",
        ".deb",
        ".rpm",
        ".msi",
        ".apk",
        ".ipa",
        ".jar",
        ".war",
        ".ear",
    ],
}

# Flatten the mapping for O(1) look‑ups.
EXTENSION_TO_CATEGORY: Dict[str, str] = {
    ext.lower(): cat for cat, exts in FILE_CATEGORIES.items() for ext in exts
}

# Names of the folders this tool creates, used to keep re-runs idempotent.
CATEGORY_NAMES = set(FILE_CATEGORIES) | {"Others"}

# Default exclude patterns (glob‑style, relative to source root)
DEFAULT_EXCLUDE = [
    ".*",  # hidden files/folders
    "*/.git",  # git repos
    "*/.hg",  # mercurial repos
    "*/.svn",  # subversion repos
    "*/venv",
    "*/env",
    "*/virtualenv",  # virtual environments
    "*/node_modules",  # Node.js projects
]


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_category_by_extension(extension: str) -> str:
    """Return the category for a given file extension."""
    return EXTENSION_TO_CATEGORY.get(extension.lower(), "Others")


def scan_directory(
    source_dirs: List[Path], exclude_patterns: List[str]
) -> Tuple[Dict[str, List[Path]], List[Path]]:
    """
    Recursively scan ``source_dirs`` and group files by category.

    Yields:
        A tuple of (category_map, all_files) where ``category_map`` is
        ``{category_name: [Path, ...]}`` and ``all_files`` is a flat list
        of every discovered file (useful for conflict‑checking).
    """
    category_map: Dict[str, List[Path]] = defaultdict(list)
    all_files: List[Path] = []

    for root in source_dirs:
        log.debug(f"Scanning {root}")
        for path in root.rglob("*"):
            # Skip directories and hidden entries
            if path.is_dir() or path.name.startswith("."):
                continue

            # Skip excluded patterns
            try:
                rel = path.relative_to(root)
            except ValueError:
                # If relative_to fails (different drives on Windows), skip
                continue

            # Skip our own output folders so re-running is idempotent
            # (don't re-organize files already placed in "Images/", etc.)
            if any(part in CATEGORY_NAMES for part in rel.parts[:-1]):
                continue

            # Skip excluded patterns. A leading "*/" means "match at any depth",
            # so we test the file's name and every ancestor directory name.
            # Bare globs ("*cache*", ".*") match by name; path globs
            # ("build/*.o") match the full relative path.
            excluded = False
            for pattern in exclude_patterns:
                target = pattern[2:] if pattern.startswith("*/") else pattern
                candidates = [path.name, *rel.parts[:-1]]
                if fnmatch.fnmatch(str(rel), pattern) or any(
                    fnmatch.fnmatch(c, target) for c in candidates
                ):
                    excluded = True
                    break
            if excluded:
                continue

            category = get_category_by_extension(path.suffix)
            category_map[category].append(path)
            all_files.append(path)

    return dict(category_map), all_files


def generate_preview(
    category_map: Dict[str, List[Path]], target_root: Path
) -> List[Tuple[Path, Path]]:
    """
    Produce a list of (source_path, destination_path) tuples without touching
    the filesystem. Conflict‑resolution adds a counter suffix before the
    extension.
    """
    moves: List[Tuple[Path, Path]] = []

    for category, files in category_map.items():
        dest_dir = target_root / category
        for src in files:
            raw_dest = dest_dir / src.name
            dest = raw_dest
            counter = 1
            while dest.exists():
                stem = raw_dest.stem
                suffix = raw_dest.suffix
                dest = dest_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            moves.append((src, dest))

    return moves


def generate_date_preview(
    files: List[Path], target_root: Path
) -> List[Tuple[Path, Path]]:
    """
    Plan moves that group files into ``year/month`` folders based on their
    modification time. Conflict resolution adds a counter suffix as usual.
    """
    moves: List[Tuple[Path, Path]] = []
    for src in files:
        try:
            mtime = src.stat().st_mtime
        except OSError:
            continue
        dt = datetime.fromtimestamp(mtime)
        dest_dir = target_root / f"{dt.year}" / f"{dt.month:02d}"
        raw_dest = dest_dir / src.name
        dest = raw_dest
        counter = 1
        while dest.exists():
            stem = raw_dest.stem
            suffix = raw_dest.suffix
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        moves.append((src, dest))

    return moves


def print_preview(moves: List[Tuple[Path, Path]]) -> None:
    """Render a human‑readable preview of the planned moves."""
    if not moves:
        print("\n✨ No moves required – everything is already organized.")
        return

    print("\n" + "=" * 60)
    print(f"📦 Preview: {len(moves)} files will be moved")
    print("=" * 60)

    by_dest: Dict[Path, List[Tuple[Path, Path]]] = defaultdict(list)
    for src, dest in moves:
        by_dest[dest.parent].append((src, dest))

    for dest_dir, pairs in sorted(by_dest.items()):
        print(f"\n📁 {dest_dir.relative_to(dest_dir.parent.parent)}")
        for src, dest in pairs:
            try:
                rel: Path | str = src.relative_to(dest_dir.parent.parent)
            except ValueError:
                rel = src.name
            print(f"   📄 {rel}  →  {dest.name}")

    print("\n" + "=" * 60)


def execute_moves(
    moves: List[Tuple[Path, Path]], dry_run: bool = False
) -> Tuple[int, int]:
    """Perform the moves on disk, handling conflicts safely and recording history.

    When ``dry_run`` is True, no files are moved and no history is recorded;
    the function returns (0, 0) so callers can preview intent without side effects.
    """
    success = 0
    failed = 0

    if dry_run:
        return success, failed

    for src, dest in moves:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            print(f"✅ {src.name} → {dest.parent.name}/{dest.name}")
            record_move(src, dest)
            success += 1
        except PermissionError as exc:
            log.error(f"Permission denied moving {src}: {exc}")
            failed += 1
        except OSError as exc:
            log.error(f"OS error moving {src}: {exc}")
            failed += 1

    return success, failed


def format_summary(moves: List[Tuple[Path, Path]], success: int, failed: int) -> str:
    """Render the end-of-run summary, including a per-category breakdown."""
    by_category: Dict[str, int] = defaultdict(int)
    for _, dest in moves:
        by_category[dest.parent.name] += 1

    lines = ["=" * 50, f"✅ {success} files moved, {failed} failures."]
    if by_category:
        lines.append("By category:")
        for cat in sorted(by_category):
            lines.append(f"   {cat}: {by_category[cat]}")
    lines.append("=" * 50)
    return "\n".join(lines)


def write_report(
    moves: List[Tuple[Path, Path]],
    path: Path,
    dry_run: bool = False,
    success: int = 0,
    failed: int = 0,
) -> None:
    """Write a JSON report of the planned (or applied) moves to ``path``."""
    by_category: Dict[str, int] = defaultdict(int)
    for _, dest in moves:
        by_category[dest.parent.name] += 1

    report = {
        "timestamp": time.time(),
        "dry_run": dry_run,
        "total": len(moves),
        "success": success,
        "failed": failed,
        "by_category": dict(by_category),
        "moves": [
            {"source": str(src), "destination": str(dest)} for src, dest in moves
        ],
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except OSError as exc:
        log.error(f"Could not write report: {exc}")


# ----------------------------------------------------------------------
# History tracking for undo functionality
# ----------------------------------------------------------------------
HISTORY_FILE = Path.home() / ".file_organizer_history.json"


def load_history(history_file: Path = HISTORY_FILE) -> List[Dict[str, Any]]:
    """Load move history from JSON file."""
    if not history_file.exists():
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return cast(List[Dict[str, Any]], json.load(f))
    except (json.JSONDecodeError, OSError):
        return []


def save_history(
    history: List[Dict[str, Any]], history_file: Path = HISTORY_FILE
) -> None:
    """Save move history to JSON file."""
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except OSError as exc:
        log.error(f"Could not save history: {exc}")


def record_move(src: Path, dest: Path) -> None:
    """Record a file move for potential undo."""
    history = load_history()
    history.append(
        {
            "timestamp": time.time(),
            "source": str(src),
            "destination": str(dest),
        }
    )
    # Keep only last 1000 operations
    if len(history) > 1000:
        history = history[-1000:]
    save_history(history)


def undo_moves(history_file: Path = HISTORY_FILE) -> Tuple[int, int]:
    """Reverse recorded moves using the history file.

    Moves are unwound newest-first and a move is only reversed when its
    destination still exists and its original source does not, so undo never
    clobbers an existing file. Returns ``(success, failed)``.
    """
    history = load_history(history_file)
    if not history:
        log.info("Nothing to undo – history is empty.")
        return 0, 0

    success = 0
    failed = 0
    # Newest entries first so nested moves unwind correctly.
    for entry in reversed(history):
        dest = Path(entry["destination"])
        src = Path(entry["source"])
        if not dest.exists():
            continue
        if src.exists():
            log.warning(f"Skip undo – source already exists: {src}")
            failed += 1
            continue
        try:
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest), str(src))
            print(f"↩️  {dest.name} → {src.parent.name}/{src.name}")
            success += 1
        except (PermissionError, OSError) as exc:
            log.error(f"Undo failed for {dest}: {exc}")
            failed += 1

    # Clear history only when nothing failed.
    if failed == 0:
        save_history([], history_file)

    return success, failed


# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Organize files into categorical folders."
    )
    parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="+",
        type=Path,
        help="One or more directories to scan.",
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="extend",
        default=[],
        help="Additional glob patterns to exclude (e.g. '*cache*').",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would happen without moving any files.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase output verbosity (can be repeated).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Base directory for output (defaults to the first input path).",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Reverse the last organization using the move history.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress the preview; only print the final summary.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Write a JSON report of the planned/applied moves to this file.",
    )
    parser.add_argument(
        "--by-date",
        action="store_true",
        help="Organize files into year/month folders by modification time.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt before moving.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="file-organizer 0.1.0",
    )
    return parser


def main() -> None:
    # Windows consoles default to cp1252, which can't encode the emoji used
    # below. Force UTF-8 so output is portable across platforms.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass

    parser = build_parser()
    args = parser.parse_args()

    # Adjust logging level based on -v flags
    if args.verbose == 0:
        log.setLevel(logging.INFO)
    elif args.verbose == 1:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.DEBUG)

    # Undo mode: reverse the last organization and exit.
    if args.undo:
        success, failed = undo_moves()
        print("\n" + "=" * 50)
        print(f"↩️  {success} files restored, {failed} failures.")
        print("=" * 50)
        return

    # Merge user‑supplied excludes with defaults
    exclude_patterns = DEFAULT_EXCLUDE + args.exclude

    # Resolve target output directory
    if args.output:
        target_root = args.output.expanduser().resolve()
    else:
        if not args.paths:
            parser.error("At least one source path is required.")
        target_root = args.paths[0].expanduser().resolve()

    if not target_root.exists():
        log.error(f"Target directory does not exist: {target_root}")
        sys.exit(1)
    if not target_root.is_dir():
        log.error(f"Target is not a directory: {target_root}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1️⃣ Scan
    # ------------------------------------------------------------------
    category_map, all_files = scan_directory(args.paths, exclude_patterns)
    if not category_map:
        log.info("No files matched the supplied criteria.")
        return

    # ------------------------------------------------------------------
    # 2️⃣ Preview
    # ------------------------------------------------------------------
    if args.by_date:
        moves = generate_date_preview(all_files, target_root)
    else:
        moves = generate_preview(category_map, target_root)
    if not args.quiet:
        print_preview(moves)

    if not args.dry_run:
        # ------------------------------------------------------------------
        # 3️⃣ Execute
        # ------------------------------------------------------------------
        # Confirm before mutating, unless --yes or a non-interactive session.
        if not args.yes and sys.stdin.isatty():
            answer = input(f"Move {len(moves)} files? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                log.info("Aborted – no files were moved.")
                return

        log.info("Organizing files …")
        success, failed = execute_moves(moves)

        # ------------------------------------------------------------------
        # 4️⃣ Summary
        # ------------------------------------------------------------------
        print("\n" + format_summary(moves, success, failed))
        if args.report:
            write_report(
                moves, args.report, dry_run=False, success=success, failed=failed
            )
    else:
        log.info("🧪 Dry‑run complete – no changes were applied.")
        if args.report:
            write_report(moves, args.report, dry_run=True)


if __name__ == "__main__":
    main()
