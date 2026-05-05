"""Tests for the `utils reflow` command, its worker, and the text helper."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from rematter import _reflow_text, _reflow_worker, app

runner = CliRunner()


# ── _reflow_text helper ────────────────────────────────────────────────────────


def test_reflow_joins_consecutive_prose_lines() -> None:
    src = "This is a sentence\nthat was hard-wrapped\nacross three lines.\n"
    out = _reflow_text(src)
    assert out == "This is a sentence that was hard-wrapped across three lines.\n"


def test_reflow_preserves_blank_line_paragraphs() -> None:
    src = "First paragraph\nline two.\n\nSecond paragraph\nline two.\n"
    out = _reflow_text(src)
    assert out == "First paragraph line two.\n\nSecond paragraph line two.\n"


def test_reflow_preserves_fenced_code_blocks() -> None:
    src = "intro line\nstill intro.\n\n```python\nfoo\nbar\n```\n\ntail\nstill tail.\n"
    out = _reflow_text(src)
    assert "intro line still intro." in out
    assert "```python\nfoo\nbar\n```" in out
    assert "tail still tail." in out


def test_reflow_preserves_tilde_fenced_code_blocks() -> None:
    src = "~~~\nfoo\nbar\n~~~\n"
    out = _reflow_text(src)
    assert out == "~~~\nfoo\nbar\n~~~\n"


def test_reflow_preserves_headings() -> None:
    src = "# Heading\nbody continues\nhere.\n"
    out = _reflow_text(src)
    assert out == "# Heading\nbody continues here.\n"


def test_reflow_preserves_bullet_lists() -> None:
    src = "- item one\n- item two\n- item three\n"
    out = _reflow_text(src)
    assert out == "- item one\n- item two\n- item three\n"


def test_reflow_preserves_ordered_lists() -> None:
    src = "1. first\n2. second\n3. third\n"
    out = _reflow_text(src)
    assert out == "1. first\n2. second\n3. third\n"


def test_reflow_preserves_blockquotes() -> None:
    src = "> quoted line\n> another quoted line\n"
    out = _reflow_text(src)
    assert out == "> quoted line\n> another quoted line\n"


def test_reflow_preserves_tables() -> None:
    src = "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    out = _reflow_text(src)
    assert out == src


def test_reflow_preserves_horizontal_rules() -> None:
    src = "para one\ncontinued.\n\n---\n\npara two.\n"
    out = _reflow_text(src)
    assert "para one continued." in out
    assert "\n---\n" in out
    assert "para two." in out


def test_reflow_preserves_html_blocks() -> None:
    src = "<div>\nhello\n</div>\n"
    out = _reflow_text(src)
    assert out == src


def test_reflow_no_trailing_newline_preserved() -> None:
    """If input has no trailing newline, output shouldn't add one."""
    src = "one\ntwo"
    out = _reflow_text(src)
    assert out == "one two"


def test_reflow_empty_string() -> None:
    assert _reflow_text("") == ""


# ── _reflow_worker ─────────────────────────────────────────────────────────────


def test_reflow_worker_preserves_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text(
        "---\ntitle: Hello\ntags: [a, b]\n---\nThis is a sentence\nthat was wrapped.\n"
    )
    status, _ = _reflow_worker(f, dry_run=False)
    assert status == "done"
    content = f.read_text()
    assert "title: Hello" in content
    assert "tags:" in content
    assert "This is a sentence that was wrapped." in content


def test_reflow_worker_handles_no_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("Just a sentence\nbroken in two.\n")
    status, _ = _reflow_worker(f, dry_run=False)
    assert status == "done"
    assert f.read_text() == "Just a sentence broken in two.\n"


def test_reflow_worker_skip_when_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("---\ntitle: T\n---\nAlready one line.\n")
    status, _ = _reflow_worker(f, dry_run=False)
    assert status == "skip"


def test_reflow_worker_dry_run_makes_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    original = "para line one\nline two.\n"
    f.write_text(original)
    status, _ = _reflow_worker(f, dry_run=True)
    assert status == "dry-run"
    assert f.read_text() == original


def test_reflow_worker_does_not_treat_frontmatter_yaml_as_prose(tmp_path: Path) -> None:
    """Regression: YAML lines inside frontmatter must not be joined into prose."""
    f = tmp_path / "note.md"
    f.write_text(
        "---\ntitle: Hello\nauthor: Someone\ntags: [a, b]\n---\nBody.\n"
    )
    _reflow_worker(f, dry_run=False)
    content = f.read_text()
    assert "title: Hello\n" in content
    assert "author: Someone\n" in content


# ── CLI integration ────────────────────────────────────────────────────────────


def test_cli_utils_reflow_basic(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("para one\nbroken across lines.\n")
    (tmp_path / "b.md").write_text("---\ntitle: B\n---\nAlready one line.\n")
    result = runner.invoke(app, ["utils", "reflow", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "a.md").read_text() == "para one broken across lines.\n"


def test_cli_utils_reflow_dry_run(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("para one\nbroken.\n")
    before = (tmp_path / "a.md").read_text()
    result = runner.invoke(app, ["utils", "reflow", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert (tmp_path / "a.md").read_text() == before
