"""Tests for the `utils move-linked-dir` command.

Terminology
- source: the anchor world (defaults to pwd; --from to override).
- target: the dir being moved, relative to source.
- to: optional new location for target, relative to source. Omit to flatten
  target's contents into source.
"""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from rematter import _move_linked_dir, app

runner = CliRunner()


def _make(p: Path, content: str = "") -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ── flatten (default --to omitted) ─────────────────────────────────────────────


def test_flatten_target_into_source(tmp_path: Path) -> None:
    """Default behavior: move all children of target up to source."""
    src = tmp_path / "src"
    note = _make(src / "note.md", "![alt](_media/img.png)\n\n[other](_media/other.md)\n")
    _make(src / "_media" / "img.png", "binary")
    _make(src / "_media" / "other.md", "back: [n](../note.md)\n")

    result = _move_linked_dir(Path("_media"), source=src)
    assert result.errors == []

    assert (src / "img.png").exists()
    assert (src / "other.md").exists()
    assert not (src / "_media").exists()

    assert note.read_text() == "![alt](img.png)\n\n[other](other.md)\n"
    # other.md moved up one level — its ../note.md becomes note.md
    assert (src / "other.md").read_text() == "back: [n](note.md)\n"


def test_flatten_does_not_touch_unrelated_links(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(
        src / "note.md",
        "![](pics/img.png)\n![](_media/keep.png)\n[ext](https://example.com)\n",
    )
    _make(src / "pics" / "img.png", "x")
    _make(src / "_media" / "keep.png", "x")

    _move_linked_dir(Path("_media"), source=src)

    text = note.read_text()
    assert "![](pics/img.png)" in text
    assert "![](keep.png)" in text
    assert "[ext](https://example.com)" in text


def test_flatten_skips_wikilinks(tmp_path: Path) -> None:
    """Bare wikilinks resolve by filename — never touched."""
    src = tmp_path / "src"
    note = _make(src / "note.md", "see [[other]] and ![[img.png]]\n")
    _make(src / "_media" / "other.md", "")
    _make(src / "_media" / "img.png", "x")

    _move_linked_dir(Path("_media"), source=src)
    assert note.read_text() == "see [[other]] and ![[img.png]]\n"


def test_flatten_with_absolute_target(tmp_path: Path) -> None:
    """Absolute target paths work as long as they live inside source."""
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](_media/img.png)\n")
    _make(src / "_media" / "img.png", "x")

    _move_linked_dir(src / "_media", source=src)
    assert (src / "img.png").exists()
    assert note.read_text() == "![](img.png)\n"


def test_default_source_is_cwd(tmp_path: Path) -> None:
    """When source is omitted, Path.cwd() is the anchor."""
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](_media/img.png)\n")
    _make(src / "_media" / "img.png", "x")

    cwd_before = Path.cwd()
    try:
        os.chdir(src)
        _move_linked_dir(Path("_media"))
    finally:
        os.chdir(cwd_before)

    assert (src / "img.png").exists()
    assert note.read_text() == "![](img.png)\n"


# ── rename ─────────────────────────────────────────────────────────────────────


def test_rename_target(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](old/img.png)\n")
    _make(src / "old" / "img.png", "x")

    _move_linked_dir(Path("old"), source=src, to=Path("new"))

    assert (src / "new" / "img.png").exists()
    assert not (src / "old").exists()
    assert note.read_text() == "![](new/img.png)\n"


# ── nested move ────────────────────────────────────────────────────────────────


def test_move_target_into_another_subdir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](pics/img.png)\n")
    _make(src / "pics" / "img.png", "x")
    _make(src / "assets" / ".keep", "")

    _move_linked_dir(Path("pics"), source=src, to=Path("assets/pics"))

    assert (src / "assets" / "pics" / "img.png").exists()
    assert not (src / "pics").exists()
    assert note.read_text() == "![](assets/pics/img.png)\n"


# ── dry run ────────────────────────────────────────────────────────────────────


def test_dry_run_leaves_filesystem_and_files_alone(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](_media/img.png)\n")
    _make(src / "_media" / "img.png", "x")

    result = _move_linked_dir(Path("_media"), source=src, dry_run=True)
    assert result.errors == []

    assert (src / "_media" / "img.png").exists()
    assert not (src / "img.png").exists()
    assert note.read_text() == "![](_media/img.png)\n"
    assert any("img.png" in p for p in result.planned_moves)


# ── errors ─────────────────────────────────────────────────────────────────────


def test_error_when_target_does_not_exist(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    result = _move_linked_dir(Path("missing"), source=src)
    assert result.errors


def test_error_when_target_outside_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    result = _move_linked_dir(outside, source=src)
    assert result.errors
    assert any("outside" in e.lower() for e in result.errors)


def test_error_when_dest_outside_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "x").mkdir()
    outside = tmp_path / "elsewhere"
    result = _move_linked_dir(Path("x"), source=src, to=outside)
    assert result.errors
    assert any("outside" in e.lower() for e in result.errors)


def test_error_when_dest_already_exists_for_rename(tmp_path: Path) -> None:
    """If --to is given and dest already exists, refuse to merge."""
    src = tmp_path / "src"
    _make(src / "old" / "a.md", "")
    _make(src / "new" / "b.md", "")
    result = _move_linked_dir(Path("old"), source=src, to=Path("new"))
    assert result.errors


def test_error_when_flatten_collision(tmp_path: Path) -> None:
    src = tmp_path / "src"
    _make(src / "img.png", "existing")
    _make(src / "_media" / "img.png", "incoming")
    result = _move_linked_dir(Path("_media"), source=src)
    assert result.errors
    assert (src / "img.png").read_text() == "existing"
    assert (src / "_media" / "img.png").exists()


def test_error_when_target_equals_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    result = _move_linked_dir(src, source=src)
    assert result.errors


# ── CLI integration ────────────────────────────────────────────────────────────


def test_cli_basic_uses_cwd_as_source(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](_media/img.png)\n")
    _make(src / "_media" / "img.png", "x")

    cwd_before = Path.cwd()
    try:
        os.chdir(src)
        result = runner.invoke(app, ["utils", "move-linked-dir", "_media"])
    finally:
        os.chdir(cwd_before)
    assert result.exit_code == 0, result.output
    assert (src / "img.png").exists()
    assert note.read_text() == "![](img.png)\n"


def test_cli_from_flag(tmp_path: Path) -> None:
    src = tmp_path / "skill" / "cool-skill"
    note = _make(src / "note.md", "![](references/img.png)\n")
    _make(src / "references" / "img.png", "x")

    result = runner.invoke(
        app,
        [
            "utils",
            "move-linked-dir",
            "references",
            "--from",
            str(src),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (src / "img.png").exists()
    assert note.read_text() == "![](img.png)\n"


def test_cli_from_and_to(tmp_path: Path) -> None:
    src = tmp_path / "skill" / "cool-skill"
    note = _make(src / "note.md", "![](references/img.png)\n")
    _make(src / "references" / "img.png", "x")

    result = runner.invoke(
        app,
        [
            "utils",
            "move-linked-dir",
            "references",
            "--from",
            str(src),
            "--to",
            "docs",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (src / "docs" / "img.png").exists()
    assert note.read_text() == "![](docs/img.png)\n"


def test_cli_dry_run(tmp_path: Path) -> None:
    src = tmp_path / "src"
    note = _make(src / "note.md", "![](_media/img.png)\n")
    _make(src / "_media" / "img.png", "x")

    result = runner.invoke(
        app,
        ["utils", "move-linked-dir", "_media", "--from", str(src), "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    assert (src / "_media" / "img.png").exists()
    assert not (src / "img.png").exists()
    assert note.read_text() == "![](_media/img.png)\n"
