"""Tests for the `utils step-headings` command, its worker, and the text helper."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from rematter import _step_headings_text, _step_headings_worker, app

runner = CliRunner()


# ── _step_headings_text helper ─────────────────────────────────────────────────


def test_no_change_when_already_stepped() -> None:
    src = "# H1\n\n## H2\n\n### H3\n"
    assert _step_headings_text(src) == src


def test_top_level_is_preserved() -> None:
    """If the top-level heading is h2, it stays h2 (we don't promote to h1)."""
    src = "## Top\n\n### Sub\n"
    assert _step_headings_text(src) == src


def test_skipped_level_pulled_up() -> None:
    """h2 → h4 should become h2 → h3."""
    src = "## A\n\n#### B\n"
    assert _step_headings_text(src) == "## A\n\n### B\n"


def test_descendants_shift_with_parent() -> None:
    """If h4 becomes h3, its child h5 also moves up to h4."""
    src = "## A\n\n#### B\n\n##### C\n"
    assert _step_headings_text(src) == "## A\n\n### B\n\n#### C\n"


def test_sibling_returns_to_correct_level() -> None:
    """After climbing back up, sibling shifts use the new parent level."""
    src = "## A\n\n#### B\n\n##### C\n\n## D\n\n#### E\n"
    expected = "## A\n\n### B\n\n#### C\n\n## D\n\n### E\n"
    assert _step_headings_text(src) == expected


def test_top_level_h3_preserved_then_descendants_step() -> None:
    """Top is h3; child h6 (skipped levels) → h4."""
    src = "### Top\n\n###### Deep\n"
    assert _step_headings_text(src) == "### Top\n\n#### Deep\n"


def test_headings_inside_fenced_code_blocks_untouched() -> None:
    src = "## A\n\n```\n#### not a heading\n```\n\n#### B\n"
    expected = "## A\n\n```\n#### not a heading\n```\n\n### B\n"
    assert _step_headings_text(src) == expected


def test_headings_with_trailing_content_preserved() -> None:
    """Heading text/markup beyond the # markers must round-trip."""
    src = "## Title with `code` and *emphasis*\n\n#### Sub-skip\n"
    expected = "## Title with `code` and *emphasis*\n\n### Sub-skip\n"
    assert _step_headings_text(src) == expected


def test_setext_headings_left_alone() -> None:
    """Underline-style headings are not in scope; only ATX (#) is rewritten."""
    src = "Top\n===\n\n#### Skip\n"
    # No ATX top-level → stack is empty when we hit ####, so it stays ####.
    assert _step_headings_text(src) == src


def test_no_headings_no_change() -> None:
    src = "Just a paragraph.\n\nAnother one.\n"
    assert _step_headings_text(src) == src


def test_empty_input() -> None:
    assert _step_headings_text("") == ""


# ── worker ─────────────────────────────────────────────────────────────────────


def test_worker_preserves_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "n.md"
    f.write_text("---\ntitle: T\n---\n## A\n\n#### B\n")
    status, _ = _step_headings_worker(f, dry_run=False)
    assert status == "done"
    content = f.read_text()
    assert "title: T" in content
    assert "## A" in content
    assert "### B" in content


def test_worker_skip_when_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "n.md"
    f.write_text("## A\n\n### B\n")
    status, _ = _step_headings_worker(f, dry_run=False)
    assert status == "skip"


def test_worker_dry_run_makes_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "n.md"
    original = "## A\n\n#### B\n"
    f.write_text(original)
    status, _ = _step_headings_worker(f, dry_run=True)
    assert status == "dry-run"
    assert f.read_text() == original


# ── CLI integration ────────────────────────────────────────────────────────────


def test_cli_utils_step_headings(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("## A\n\n#### B\n")
    result = runner.invoke(app, ["utils", "step-headings", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert f.read_text() == "## A\n\n### B\n"
