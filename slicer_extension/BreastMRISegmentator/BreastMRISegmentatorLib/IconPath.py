"""Helpers to resolve packaged icon resources."""
from __future__ import annotations

from pathlib import Path

_ICON_DIR = Path(__file__).parent.parent / "Resources" / "Icons"


def iconPath(name: str) -> str:
    """Return the absolute path to ``Resources/Icons/<name>``."""
    return str(_ICON_DIR / name)


def icon(name: str):
    """Return a ``qt.QIcon`` for the named resource (requires Qt at runtime)."""
    import qt

    return qt.QIcon(iconPath(name))
