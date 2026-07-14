"""Comprehensive tests for file_organizer module."""

from __future__ import annotations


import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from file_organizer import (
    DEFAULT_EXCLUDE,
    FILE_CATEGORIES,
    EXTENSION_TO_CATEGORY,
    get_category_by_extension,
    scan_directory,
    generate_preview,
    generate_date_preview,
    execute_moves,
    undo_moves,
    write_report,
    format_summary,
)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_files(temp_dir: Path) -> dict[str, Path]:
    """Create sample files across different categories."""
    files = {
        "image_jpg": temp_dir / "photo.jpg",
        "image_png": temp_dir / "graphic.png",
        "video_mp4": temp_dir / "movie.mp4",
        "doc_pdf": temp_dir / "report.pdf",
        "doc_txt": temp_dir / "notes.txt",
        "audio_mp3": temp_dir / "song.mp3",
        "archive_zip": temp_dir / "backup.zip",
        "other_xyz": temp_dir / "unknown.xyz",
    }
    for path in files.values():
        path.write_text("test content")
    return files


# ----------------------------------------------------------------------
# Extension-to-category tests
# ----------------------------------------------------------------------
class TestCategoryLookup:
    """Tests for get_category_by_extension function."""

    def test_image_extensions(self) -> None:
        """All common image extensions map to Images."""
        for ext in FILE_CATEGORIES["Images"]:
            assert get_category_by_extension(ext) == "Images"

    def test_video_extensions(self) -> None:
        """All video extensions map to Videos."""
        for ext in FILE_CATEGORIES["Videos"]:
            assert get_category_by_extension(ext) == "Videos"

    def test_document_extensions(self) -> None:
        """Document extensions map to Documents."""
        for ext in FILE_CATEGORIES["Documents"]:
            assert get_category_by_extension(ext) == "Documents"

    def test_audio_extensions(self) -> None:
        """Audio extensions map to Audio."""
        for ext in FILE_CATEGORIES["Audio"]:
            assert get_category_by_extension(ext) == "Audio"

    def test_archive_extensions(self) -> None:
        """Archive extensions map to Archives."""
        for ext in FILE_CATEGORIES["Archives"]:
            assert get_category_by_extension(ext) == "Archives"

    def test_uppercase_extension(self) -> None:
        """Extension lookup is case-insensitive."""
        assert get_category_by_extension(".JPG") == "Images"
        assert get_category_by_extension(".PDF") == "Documents"

    def test_unknown_extension(self) -> None:
        """Unknown extensions default to Others."""
        assert get_category_by_extension(".xyz") == "Others"
        assert get_category_by_extension(".unknown") == "Others"


# ----------------------------------------------------------------------
# Extension-to-category dictionary tests
# ----------------------------------------------------------------------
class TestExtensionMapping:
    """Tests for the flattened EXTENSION_TO_CATEGORY dictionary."""

    def test_all_extensions_mapped(self) -> None:
        """Every extension in FILE_CATEGORIES appears in EXTENSION_TO_CATEGORY."""
        for category, extensions in FILE_CATEGORIES.items():
            for ext in extensions:
                assert ext.lower() in EXTENSION_TO_CATEGORY
                assert EXTENSION_TO_CATEGORY[ext.lower()] == category

    def test_no_duplicates(self) -> None:
        """Each extension maps to exactly one category."""
        # If there were duplicates, the dict would have fewer unique keys
        total_extensions = sum(len(exts) for exts in FILE_CATEGORIES.values())
        assert len(EXTENSION_TO_CATEGORY) == total_extensions


# ----------------------------------------------------------------------
# Scanner tests
# ----------------------------------------------------------------------
class TestScanDirectory:
    """Tests for scan_directory function."""

    def test_scan_empty_directory(self, temp_dir: Path) -> None:
        """Scanning an empty directory returns empty results."""
        category_map, all_files = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        assert category_map == {}
        assert all_files == []

    def test_scan_single_file(
        self, temp_dir: Path, sample_files: dict[str, Path]
    ) -> None:
        """Scanning finds all files in the sample set."""
        category_map, all_files = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        assert len(all_files) == len(sample_files)

    def test_scan_categorizes_correctly(
        self, temp_dir: Path, sample_files: dict[str, Path]
    ) -> None:
        """Files are placed in correct categories."""
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        assert len(category_map.get("Images", [])) == 2
        assert len(category_map.get("Videos", [])) == 1
        assert len(category_map.get("Documents", [])) == 2
        assert len(category_map.get("Audio", [])) == 1
        assert len(category_map.get("Archives", [])) == 1
        assert len(category_map.get("Others", [])) == 1

    def test_scan_skips_hidden_files(self, temp_dir: Path) -> None:
        """Hidden files (starting with .) are skipped."""
        hidden = temp_dir / ".hidden_file"
        hidden.write_text("secret")
        visible = temp_dir / "visible.txt"
        visible.write_text("public")

        category_map, all_files = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        assert len(all_files) == 1
        assert all_files[0] == visible

    def test_scan_skips_excluded_patterns(self, temp_dir: Path) -> None:
        """Excluded patterns are respected."""
        # Create a file that would normally be scanned
        regular = temp_dir / "file.txt"
        regular.write_text("content")

        # Create a file in an excluded path
        node_modules = temp_dir / "node_modules"
        node_modules.mkdir()
        excluded_file = node_modules / "package.json"
        excluded_file.write_text("{}")

        category_map, all_files = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        assert len(all_files) == 1
        assert all_files[0] == regular

    def test_scan_multiple_directories(self, temp_dir: Path) -> None:
        """Scanning multiple directories merges results."""
        dir1 = temp_dir / "source1"
        dir2 = temp_dir / "source2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "a.jpg").write_text("x")
        (dir2 / "b.mp4").write_text("y")

        category_map, all_files = scan_directory([dir1, dir2], DEFAULT_EXCLUDE)
        assert len(all_files) == 2


# ----------------------------------------------------------------------
# Preview generation tests
# ----------------------------------------------------------------------
class TestGeneratePreview:
    """Tests for generate_preview function."""

    def test_preview_empty_map(self, temp_dir: Path) -> None:
        """Empty category map produces empty moves."""
        moves = generate_preview({}, temp_dir)
        assert moves == []

    def test_preview_creates_correct_destinations(
        self, temp_dir: Path, sample_files: dict[str, Path]
    ) -> None:
        """Preview generates correct destination paths."""
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        moves = generate_preview(category_map, temp_dir)

        # Check that all destinations are in correct category folders
        for src, dest in moves:
            assert dest.parent.name in FILE_CATEGORIES or dest.parent.name == "Others"
            assert dest.parent != src.parent

    def test_preview_handles_conflicts(self, temp_dir: Path) -> None:
        """Preview adds counter suffix for existing files."""
        # Create a file that already exists in the destination
        image_dir = temp_dir / "Images"
        image_dir.mkdir()
        (image_dir / "photo.jpg").write_text("existing")

        # Create source file with same name
        source = temp_dir / "photo.jpg"
        source.write_text("new")

        category_map = {"Images": [source]}
        moves = generate_preview(category_map, temp_dir)

        assert len(moves) == 1
        src, dest = moves[0]
        # Should have counter suffix
        assert dest.name == "photo_1.jpg"


class TestGenerateDatePreview:
    """Tests for generate_date_preview function."""

    def test_generate_date_preview(self, temp_dir: Path) -> None:
        """Files are planned into year/month folders by modification time."""
        import os
        from datetime import datetime

        src = temp_dir / "photo.jpg"
        src.write_text("x")
        os.utime(src, (1710000000, 1710000000))

        moves = generate_date_preview([src], temp_dir)

        dt = datetime.fromtimestamp(1710000000)
        expected_dir = temp_dir / f"{dt.year}" / f"{dt.month:02d}"
        assert len(moves) == 1
        assert moves[0][1].parent == expected_dir


# ----------------------------------------------------------------------
# Execute moves tests
# ----------------------------------------------------------------------
class TestExecuteMoves:
    """Tests for execute_moves function."""

    def test_execute_moves_success(
        self, temp_dir: Path, sample_files: dict[str, Path]
    ) -> None:
        """Files are moved correctly."""
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        moves = generate_preview(category_map, temp_dir)

        success, failed = execute_moves(moves)

        assert success == len(moves)
        assert failed == 0

        # Verify files are in new locations
        for src, dest in moves:
            assert not src.exists()
            assert dest.exists()

    def test_execute_moves_dry_run(
        self, temp_dir: Path, sample_files: dict[str, Path]
    ) -> None:
        """Dry run does not move files."""
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        moves = generate_preview(category_map, temp_dir)

        # Normal execution
        success, failed = execute_moves(moves, dry_run=True)

        # Files should still exist in original location
        for src, _ in moves:
            assert src.exists()

    def test_execute_moves_permission_error(self, temp_dir: Path) -> None:
        """Permission errors are handled gracefully."""
        # Create a read-only file (may not work on all platforms)
        readonly = temp_dir / "readonly.txt"
        readonly.write_text("content")

        # Try to move to a non-existent destination that would require permission
        # This test verifies the try/except doesn't crash
        moves = [(readonly, temp_dir / "Images" / "moved.txt")]
        success, failed = execute_moves(moves)

        # Should succeed (Windows doesn't truly support read-only files the same way)
        # On Unix, we'd expect failed=1


# ----------------------------------------------------------------------
# Integration tests
# ----------------------------------------------------------------------
class TestIntegration:
    """End-to-end integration tests."""

    def test_full_organization_workflow(self, temp_dir: Path) -> None:
        """Complete workflow from scan to organization."""
        # Setup
        (temp_dir / "photo.jpg").write_text("image")
        (temp_dir / "song.mp3").write_text("audio")
        (temp_dir / "report.pdf").write_text("doc")

        # Scan
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)

        # Preview
        moves = generate_preview(category_map, temp_dir)
        assert len(moves) == 3

        # Execute
        success, failed = execute_moves(moves)
        assert success == 3
        assert failed == 0

        # Verify
        assert (temp_dir / "Images" / "photo.jpg").exists()
        assert (temp_dir / "Audio" / "song.mp3").exists()
        assert (temp_dir / "Documents" / "report.pdf").exists()

    def test_no_double_organization(self, temp_dir: Path) -> None:
        """Running twice doesn't move already-organized files."""
        # First run
        (temp_dir / "photo.jpg").write_text("image")
        category_map, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        moves = generate_preview(category_map, temp_dir)
        execute_moves(moves)

        # Second run
        category_map2, _ = scan_directory([temp_dir], DEFAULT_EXCLUDE)
        moves2 = generate_preview(category_map2, temp_dir)
        assert len(moves2) == 0  # Nothing to do


# ----------------------------------------------------------------------
# Undo tests
# ----------------------------------------------------------------------
class TestUndoMoves:
    """Tests for the undo_moves function."""

    def test_undo_restores_files(self, temp_dir: Path) -> None:
        """A recorded move is reversed and the file returns to its source."""
        src = temp_dir / "photo.jpg"
        dest = temp_dir / "Images" / "photo.jpg"
        dest.parent.mkdir()
        dest.write_text("image")  # simulate an already-organized file (source is gone)

        history_file = temp_dir / "history.json"
        history_file.write_text(
            json.dumps(
                [
                    {
                        "timestamp": 1.0,
                        "source": str(src),
                        "destination": str(dest),
                    }
                ]
            )
        )

        success, failed = undo_moves(history_file)

        assert success == 1
        assert failed == 0
        assert src.exists()
        assert not dest.exists()
        # History is cleared after a clean undo
        assert json.loads(history_file.read_text()) == []

    def test_undo_empty_history(self, temp_dir: Path) -> None:
        """Undoing with no history is a no-op."""
        history_file = temp_dir / "history.json"
        history_file.write_text("[]")

        success, failed = undo_moves(history_file)

        assert success == 0
        assert failed == 0

    def test_undo_skips_when_source_exists(self, temp_dir: Path) -> None:
        """Undo does not clobber a file already present at the source."""
        src = temp_dir / "photo.jpg"
        dest = temp_dir / "Images" / "photo.jpg"
        dest.parent.mkdir()
        src.write_text("original")  # already here
        dest.write_text("moved")

        history_file = temp_dir / "history.json"
        history_file.write_text(
            json.dumps(
                [
                    {
                        "timestamp": 1.0,
                        "source": str(src),
                        "destination": str(dest),
                    }
                ]
            )
        )

        success, failed = undo_moves(history_file)

        assert success == 0
        assert failed == 1
        assert src.read_text() == "original"  # untouched
        assert dest.exists()


# ----------------------------------------------------------------------
# Report / summary tests
# ----------------------------------------------------------------------
class TestReportAndSummary:
    """Tests for write_report and format_summary."""

    def test_write_report_contents(self, temp_dir: Path) -> None:
        """write_report emits a JSON report with counts and moves."""
        src = temp_dir / "photo.jpg"
        dest = temp_dir / "Images" / "photo.jpg"
        moves = [(src, dest)]

        report_path = temp_dir / "report.json"
        write_report(moves, report_path, dry_run=True)

        data = json.loads(report_path.read_text())
        assert data["total"] == 1
        assert data["dry_run"] is True
        assert data["by_category"] == {"Images": 1}
        assert data["moves"][0]["source"] == str(src)
        assert data["moves"][0]["destination"] == str(dest)

    def test_format_summary_breakdown(self, temp_dir: Path) -> None:
        """format_summary shows the per-category breakdown."""
        src = temp_dir / "photo.jpg"
        dest = temp_dir / "Images" / "photo.jpg"
        out = format_summary([(src, dest)], success=1, failed=0)

        assert "1 files moved" in out
        assert "Images: 1" in out
