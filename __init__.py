"""Hermes loader wrapper for the src-layout implementation."""

import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from hermes_auto_routing import register  # noqa: E402

__all__ = ["register"]
