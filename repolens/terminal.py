"""Terminal colour policy for RepoLens.

RepoLens is regularly piped into files, CI logs and accessibility-focused
terminals, so the decision "may I emit ANSI colour?" belongs in one place.
Every :class:`rich.console.Console` the tool builds goes through
:func:`make_console`, and ``--no-color`` reaches consoles that already exist
(because they are created at import time, before Click parses the flags) via
:func:`disable_color`.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

import click
from rich.console import Console

NO_COLOR_ENV = "NO_COLOR"
TERM_ENV = "TERM"

#: ``TERM`` values that mean "there is no terminal here".
DUMB_TERMS = frozenset({"dumb", "unknown"})

F = TypeVar("F", bound=Callable[..., Any])

_consoles: list[Console] = []
_disabled = False


def color_disabled(
    environ: Mapping[str, str] | None = None,
    *,
    no_color_flag: bool = False,
) -> bool:
    """Return ``True`` when ANSI colour must not be emitted.

    The ``--no-color`` flag wins, then a non-empty ``NO_COLOR``, then
    ``TERM=dumb`` (or the equally speechless ``TERM=unknown``).  An empty
    ``NO_COLOR`` -- ``NO_COLOR=`` -- counts as "not set", matching the
    no-color.org convention.
    """
    if no_color_flag:
        return True
    env = os.environ if environ is None else environ
    if env.get(NO_COLOR_ENV, "").strip():
        return True
    return env.get(TERM_ENV, "").strip().lower() in DUMB_TERMS


def make_console(**kwargs: Any) -> Console:
    """Build a console that honours the terminal colour policy."""
    kwargs.setdefault("legacy_windows", False)
    if "no_color" not in kwargs:
        kwargs["no_color"] = _disabled or color_disabled()
    console = Console(**kwargs)
    _consoles.append(console)
    return console


def consoles() -> Sequence[Console]:
    """Every console RepoLens has created so far."""
    return tuple(_consoles)


def disable_color(disabled: bool = True) -> None:
    """Force colour off (or allow it again) for existing consoles."""
    global _disabled
    _disabled = disabled
    if disabled:
        for console in _consoles:
            console.no_color = True


def no_color_option(func: F) -> F:
    """Attach ``--no-color`` to a command and apply it before it runs.

    ``expose_value`` is off so the flag does not change the signature of the
    command callbacks, and ``is_eager`` makes sure the report is already
    colour-free by the time it is rendered.
    """

    def _apply(ctx: click.Context, param: click.Parameter, value: bool) -> bool:
        if value:
            disable_color()
        return value

    return click.option(
        "--no-color",
        "no_color",
        is_flag=True,
        default=False,
        expose_value=False,
        is_eager=True,
        callback=_apply,
        help="Disable ANSI colour in the report (also honours NO_COLOR).",
    )(func)
