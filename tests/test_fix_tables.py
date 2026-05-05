"""Tests for the `utils fix-tables` command, its worker, and the text helper."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from rematter import _fix_tables_text, _fix_tables_worker, app

runner = CliRunner()


# ── compact style (default) ────────────────────────────────────────────────────


def test_compact_adds_inner_padding() -> None:
    src = "|foo|bar|\n|---|---|\n|1|2|\n"
    out = _fix_tables_text(src, style="compact")
    assert out == "| foo | bar |\n| --- | --- |\n| 1 | 2 |\n"


def test_compact_normalizes_extra_padding() -> None:
    src = "|  foo  |   bar   |\n| --- | --- |\n"
    out = _fix_tables_text(src, style="compact")
    assert out == "| foo | bar |\n| --- | --- |\n"


def test_compact_preserves_alignment_colons() -> None:
    src = "|a|b|c|\n|:---|:---:|---:|\n|1|2|3|\n"
    out = _fix_tables_text(src, style="compact")
    assert out == "| a | b | c |\n| :--- | :---: | ---: |\n| 1 | 2 | 3 |\n"


def test_compact_leaves_already_compact_tables_unchanged() -> None:
    src = "| foo | bar |\n| --- | --- |\n| 1 | 2 |\n"
    assert _fix_tables_text(src, style="compact") == src


# ── aligned style ──────────────────────────────────────────────────────────────


def test_aligned_pads_columns_to_widest_cell() -> None:
    src = "| a | bb |\n| --- | --- |\n| ccc | d |\n"
    out = _fix_tables_text(src, style="aligned")
    # col 0 width = max(1, 3, 3) = 3; col 1 width = max(2, 3, 1) = 3
    assert out == "| a   | bb  |\n| --- | --- |\n| ccc | d   |\n"


def test_aligned_separator_preserves_alignment_colons() -> None:
    src = "| a | b | c |\n| :--- | :---: | ---: |\n| xxxx | yyyy | zzzz |\n"
    out = _fix_tables_text(src, style="aligned")
    lines = out.splitlines()
    # Column widths: col0 max(1,4,4)=4; col1 max(1,5,4)=5; col2 max(1,4,4)=4
    assert lines[0] == "| a    | b     | c    |"
    assert lines[1] == "| :--- | :---: | ---: |"
    assert lines[2] == "| xxxx | yyyy  | zzzz |"


# ── code blocks ────────────────────────────────────────────────────────────────


def test_does_not_touch_tables_inside_fenced_code_blocks() -> None:
    src = "```\n|foo|bar|\n|---|---|\n```\n"
    out = _fix_tables_text(src, style="compact")
    assert out == src


def test_processes_table_after_code_block() -> None:
    src = "```\nignored\n```\n\n|foo|bar|\n|---|---|\n"
    out = _fix_tables_text(src, style="compact")
    assert "| foo | bar |" in out
    assert "| --- | --- |" in out


# ── worker ─────────────────────────────────────────────────────────────────────


def test_worker_preserves_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("---\ntitle: T\n---\n|foo|bar|\n|---|---|\n|1|2|\n")
    status, _ = _fix_tables_worker(f, style="compact", dry_run=False)
    assert status == "done"
    content = f.read_text()
    assert "title: T" in content
    assert "| foo | bar |" in content


def test_worker_handles_no_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("|a|b|\n|---|---|\n")
    status, _ = _fix_tables_worker(f, style="compact", dry_run=False)
    assert status == "done"
    assert f.read_text() == "| a | b |\n| --- | --- |\n"


def test_worker_skip_when_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    f.write_text("| a | b |\n| --- | --- |\n")
    status, _ = _fix_tables_worker(f, style="compact", dry_run=False)
    assert status == "skip"


def test_worker_dry_run_makes_no_changes(tmp_path: Path) -> None:
    f = tmp_path / "note.md"
    original = "|foo|bar|\n|---|---|\n"
    f.write_text(original)
    status, _ = _fix_tables_worker(f, style="compact", dry_run=True)
    assert status == "dry-run"
    assert f.read_text() == original


# ── CLI integration ────────────────────────────────────────────────────────────


def test_cli_utils_fix_tables_default_compact(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("|foo|bar|\n|---|---|\n")
    result = runner.invoke(app, ["utils", "fix-tables", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert f.read_text() == "| foo | bar |\n| --- | --- |\n"


def test_cli_utils_fix_tables_aligned(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("|a|bb|\n|---|---|\n|ccc|d|\n")
    result = runner.invoke(
        app, ["utils", "fix-tables", str(tmp_path), "--style", "aligned"]
    )
    assert result.exit_code == 0, result.output
    assert f.read_text() == "| a   | bb  |\n| --- | --- |\n| ccc | d   |\n"


def test_cli_utils_fix_tables_invalid_style(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("|a|b|\n|---|---|\n")
    result = runner.invoke(
        app, ["utils", "fix-tables", str(tmp_path), "--style", "bogus"]
    )
    assert result.exit_code != 0
