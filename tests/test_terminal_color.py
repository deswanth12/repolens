"""Tests for the terminal colour policy: NO_COLOR, TERM=dumb and --no-color."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from click.testing import CliRunner

import repolens.formatters.terminal as formatter_terminal
from repolens import terminal
from repolens.cli import console as cli_console
from repolens.cli import main

# The 256-colour / truecolor escape for cyan, as Rich renders "[cyan]".
CYAN_SGR = "\x1b[1;36m"


@pytest.fixture
def no_color_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Start from a terminal that has asked for neither of the two variables."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    return monkeypatch


@pytest.fixture(autouse=True)
def restore_consoles():
    """``--no-color`` is global by design, so put the consoles back afterwards."""
    before = [(console, console.no_color) for console in terminal.consoles()]
    yield
    terminal.disable_color(False)
    for console, no_color in before:
        console.no_color = no_color


def render(console) -> str:
    """Print one cyan word and return the raw bytes Rich produced."""
    console.print("[bold cyan]report[/bold cyan]")
    return console.file.getvalue()


def make_capturing_console():
    buffer = io.StringIO()
    # Pin the colour system so the expected escape is the same everywhere.
    return terminal.make_console(file=buffer, force_terminal=True, color_system="standard", width=80), buffer


def test_no_color_variable_disables_color():
    assert terminal.color_disabled({"NO_COLOR": "1"}) is True


def test_empty_no_color_variable_keeps_color():
    """``NO_COLOR=`` means "not set", per the no-color.org convention."""
    assert terminal.color_disabled({"NO_COLOR": ""}) is False


def test_dumb_terminal_disables_color():
    assert terminal.color_disabled({"TERM": "dumb"}) is True
    assert terminal.color_disabled({"TERM": "DUMB"}) is True


def test_ordinary_terminal_keeps_color():
    assert terminal.color_disabled({"TERM": "xterm-256color"}) is False
    assert terminal.color_disabled({}) is False


def test_no_color_flag_disables_color():
    assert terminal.color_disabled({}, no_color_flag=True) is True


def test_console_emits_color_by_default(no_color_env):
    console, buffer = make_capturing_console()
    assert CYAN_SGR in render(console)


def test_console_goes_plain_under_no_color(no_color_env):
    no_color_env.setenv("NO_COLOR", "1")
    console, _ = make_capturing_console()
    assert CYAN_SGR not in render(console)


def test_console_goes_plain_under_dumb_terminal(no_color_env):
    no_color_env.setenv("TERM", "dumb")
    console, _ = make_capturing_console()
    assert CYAN_SGR not in render(console)


def test_disable_color_reaches_every_created_console(no_color_env):
    terminal.disable_color()
    assert formatter_terminal.console.no_color is True
    assert formatter_terminal.err_console.no_color is True
    assert cli_console.no_color is True


def test_no_color_flag_is_offered_on_the_root_cli():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--no-color" in result.output


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["--no-color", "{path}"], id="before-the-report"),
        pytest.param(["{path}", "--no-color"], id="after-the-report"),
        pytest.param(["--no-color", "scan", "{path}"], id="root-then-subcommand"),
        pytest.param(["--no-color", "report", "{path}"], id="root-then-report"),
    ],
)
def test_no_color_flag_disables_color_for_the_command(no_color_env, tmp_path: Path, argv):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")

    args = [part.format(path=str(tmp_path)) for part in argv]
    result = CliRunner().invoke(main, args)

    assert result.exit_code == 0, result.output
    assert cli_console.no_color is True


def test_no_color_flag_after_a_subcommand_is_accepted(no_color_env, tmp_path: Path):
    (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["scan", str(tmp_path), "--no-color"])

    assert result.exit_code == 0, result.output
    assert cli_console.no_color is True


def test_the_report_still_renders_without_color(no_color_env, tmp_path: Path):
    """Colour off must not cost any content."""
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")

    result = CliRunner().invoke(main, ["--no-color", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "RECOMMENDED READING ORDER" in result.output
    assert "\x1b[" not in result.output
